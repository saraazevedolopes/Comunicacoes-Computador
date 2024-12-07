import socket
import parser
from Shared import Shared
import threading
from Message_type import Message_type
import ipaddress
import logger
from Data import Data
import time

# envia uma mensagem serializada em bytes para um agente especificado através do socket UDP
def send(s : socket.socket, address : tuple, agent_id : int, message_type : int, shared_agent : Shared, retransmission : bool, *args) -> int: # args tem um id e um dicionário
    fields : list = list()
    fields.append(bin(agent_id)[2:].zfill(5))                       # id agente
    fields.append(bin(message_type)[2:].zfill(3))                   # message type
    fields.append(0)                                                # número de sequência
    inc = 0
    seq = 0

    if retransmission:
        inc = 1
    if message_type != Message_type.END.value:
        if message_type == Message_type.TASK.value:
            fields.append(bin(int(args[0+inc]))[2:].zfill(5))               # task id
            fields.append(bin(int(args[1+inc]["task_type"]))[2:].zfill(3))  # task_type
            fields.append(bin(int(args[1+inc]["frequency"]))[2:].zfill(8))  # freq
            
            if int(args[1+inc]["task_type"]) == 3:
                fields.append(bin(int(args[1+inc]["threshold"][0]))[2:].zfill(16))
                fields.append(bin(int(args[1+inc]["threshold"][1]))[2:].zfill(16))
                fields.append(bin(int(args[1+inc]["threshold"][2]))[2:].zfill(8))
            else:    
                fields.append(bin(int(args[1+inc]["threshold"]))[2:].zfill(16)) # threshold
            
            if args[1+inc]["task_type"] == 2:                               # calcular latência
                agent_name = args[1+inc]["destination"]
                ip = socket.gethostbyname(agent_name)
                
                ip_int = int(ipaddress.IPv4Address(ip))
                ip_bin = format(ip_int, '032b')

                fields.append(ip_bin)                                   # destino para usar no ping
            elif args[1+inc]["task_type"] == 3:                             # calcular largura de banda + jitter + perdas
                is_server = bin(int(args[1+inc]["is_server"]))[2:].zfill(8)
                
                ip = socket.gethostbyname(args[1+inc]["destination"])
                ip_dst = int(ipaddress.IPv4Address(ip))
                ip_dst_bin = format(ip_dst, '032b')
                fields.append(is_server)                                # ip do servidor para usar no iperf
                fields.append(ip_dst_bin)                               # ip do cliente para usar no iperf         
            elif args[1+inc]["task_type"] == 4:                             # interface a monitorizar
                interf = args[1+inc]["interface_name"].ljust(10)
                interface : str = ''.join(format(ord(character), '08b') for character in interf) 
                fields.append(interface)                              

           
        else:
            pass

        shared_agent.acquire_lock() # necessário para que outras threads não escrevam no mesmo nrº de sequência
        
        if not retransmission:
            seq = shared_agent.get_seq()
        else:
            seq = args[0]

        fields[2] = bin(seq)[2:].zfill(16)             # número de sequência
    else:
        fields[2] = bin(0)[2:].zfill(16)

    message : str = ''
    for field in fields:
        message += field

    message_bytes = int(message, 2).to_bytes(len(message) // 8, byteorder='big')
    
    if message_type == Message_type.TASK.value and not retransmission:
        shared_agent.inc_seq(len(message_bytes))
    
    if message_type != Message_type.END.value:
        shared_agent.release_lock()
    
    # Enviar mensagem pelo socket UDP
    s.sendto(message_bytes, address)

    return seq, message_bytes

# Verifica periodicamente se há ACKs recebidos e notifica o estado partilhado
def ack_monitor(shared_agent : Shared):
    while True:
        time.sleep(.5)
        shared_agent.notify_received_condition()
        if shared_agent.get_received_ack():
            shared_agent.set_received_ack(False)
               
# Envia ACKs de volta ao agente ao detectar pacotes recebidos
def ack_sender(s : socket.socket, address : tuple, agent_id : int, shared_agent : Shared, agent_logs):
    while True:
        time.sleep(.5)
        shared_agent.acquire_lock()
        if shared_agent.get_received_packet():
            seq, packet = send(s, address, agent_id, 1, shared_agent, False)
            agent_logs.debug(f"SENDING ACK SEQ={seq}")
            #threading.Thread(target=send, args=(s, address, agent_id, 1, shared_agent, False)).start()
            shared_agent.set_received_packet(False)
        shared_agent.release_lock()

def process(message : tuple, s : socket.socket, agent_details : tuple, agent_list : dict, agents_data : dict, agent_logs : dict, log_level : int): # mensagem ser um array é funcionamennto básico do socket
    fields : list = parser.parse(message[0], True, agent_logs) #[agent_id, message_type, seq]

    if fields[1] == Message_type.REGISTER.value:
        if agent_list.get(fields[0]) == None:
            shared_agent = Shared(message[1])
            
            agent_logs[fields[0]] = logger.setup_logger('app', 'logs/server/agent'+str(fields[0])+'.log', True, level=log_level)
    
            agent_list[fields[0]] = shared_agent # cria um objeto partilhado

            agent_logs[fields[0]].info(f"Agent {fields[0]} logged in.")
            #Threads de monitoria
            threading.Thread(target=ack_monitor, args=(shared_agent,)).start()
            threading.Thread(target=ack_sender, args=(s, message[1], fields[0], shared_agent, agent_logs[fields[0]])).start()
    
            agent_list[fields[0]].inc_seq(len(message[0])) # aumenta o seq

            agents_data[str(fields[0])] = Data()

            send(s, message[1], fields[0], Message_type.ACK.value, agent_list[fields[0]], False) # envia ack de volta (message type 1)
            
            # a partir daqui, vai-se tratar de enviar tarefas, o que faz parte do registo
            address : tuple = message[1]
            tasks : dict = parser.parse_tasks(str(fields[0]))

            for key, value in tasks.items(): 
                task_title = get_task_title(value)    
                agents_data[str(fields[0])].add_task(int(key), int(value["task_type"]), value["threshold"], task_title)    
                threading.Thread(target=schedule_send, args=(s, agent_logs[fields[0]],address[0], address[1], fields[0], Message_type.TASK.value, agent_list[fields[0]], key, value)).start()
    elif fields[1] == Message_type.ACK.value:
        if agent_list.get(fields[0]) != None:    
            try:
                agent_list[fields[0]].acquire_lock()
                if fields[2] > agent_list[fields[0]].get_ack():
                    agent_list[fields[0]].set_ack(fields[2])
                    agent_list[fields[0]].notify_received_condition()
                else:
                    agent_list[fields[0]].inc_repeats()
                agent_list[fields[0]].set_received_ack(True)
            finally:
                agent_list[fields[0]].release_lock()
    elif fields[1] == Message_type.METRIC.value:
        if agent_list.get(fields[0]) != None:
            try: 
                agent_list[fields[0]].acquire_lock()
                if agent_list[fields[0]].received_seq(fields[2]):
                    return
                else:
                    agent_list[fields[0]].add_packet(fields[2])
                    expected_seq = agent_list[fields[0]].get_seq() 
            finally:    
                agent_list[fields[0]].release_lock()
        
            while fields[2] >= expected_seq:
                
                if fields[2] == expected_seq:    
                    agent_list[fields[0]].acquire_lock()
                    agent_list[fields[0]].inc_seq(len(message[0]))
                    agent_list[fields[0]].set_received_packet(True)
                    agent_list[fields[0]].release_lock()
                    break
                time.sleep(0.1)
                agent_list[fields[0]].acquire_lock()
                expected_seq = agent_list[fields[0]].get_seq() 
                agent_list[fields[0]].release_lock()
            agents_data[str(fields[0])].add_metrics(fields[3], fields[5], fields[4])
    elif fields[1] == Message_type.END.value:
        if fields[0] in agent_list:
            del agent_list[fields[0]]
            send(s,message[1], fields[0], 4, None, False)
    else:
        pass

def schedule_end(address: str, port: int, agent_name : str):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1)
    success = False
    count = 0
    seq, pacote = send(s, (address, port), int(agent_name), Message_type.END.value, None, False)
    while not success and count < 3:
        try:
            message = s.recv(1024)
            success = True
        except socket.timeout:
            count+=1
            s.sendto(pacote, (address,port))

def schedule_send(s : socket.socket, agent_logger, address: str, port: int, agent_name : str, message_type : int, shared_agent : Shared, *args):
    success = False
    
    seq, packet = send(s, (address, port), int(agent_name), message_type, shared_agent, False, *args)
    agent_logger.info(f"SENDING SEQ={seq}, MESSAGE_TYPE={message_type}, LENGTH={len(packet)} bytes")
    
    while not success:
        success = shared_agent.acquire_received_condition(seq, agent_logger)
        if not success:
            s.sendto(packet, (address,port))

def get_task_title(value : dict) -> str:
    tasks = ["CPU", "RAM", "LATENCY", "IPERF", "INTERFACE"]
    task_title = tasks[int(value["task_type"])]

    if value["task_type"] == 2:
        task_title+=f" - {value['destination']}"
    elif value["task_type"] == 3:
        if value["is_server"] == 1:
            task_title+=f"(Server) - {value['destination']}"
        else:
            task_title+=f"(Client) - {value['destination']}"
    elif value["task_type"] == 4:
            task_title+=f" - {value['interface_name']}"
    return task_title
        
def start(address: str, port: int, agent_list : dict, agent_data : dict, agent_logs : dict, log_level : int): 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #AF_INET diz que é ipv4
    #SOCK_DGRAM diz que é UDP
    s.bind((address, port)) # associei o socket a um par endereço-porta
    
    while True:  
        message = s.recvfrom(1024) # buffer de 1024 bytes para receber mensagem (array de bytes)
        threading.Thread(target=process, args=(message, s, address, agent_list, agent_data, agent_logs, log_level)).start()

    s.close() 