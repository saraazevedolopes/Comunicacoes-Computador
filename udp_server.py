import socket
import json
import parser
from Shared import Shared
import threading
from Message_type import Message_type
import ipaddress

# envia uma tarefa serializada em bytes para um agente especificado através do socket UDP
def send(s : socket.socket, address : tuple, agent_id : int, message_type : int, agent_data : Shared, *args): # args tem um id e um dicionário
    fields : list = list()
    fields.append(bin(agent_id)[2:].zfill(5))                       # id agente
    fields.append(bin(message_type)[2:].zfill(3))                   # message type
    fields.append(0)                                                # número de sequência
    
    if message_type == Message_type.TASK.value:
        print(args)
        print(len(args))
        fields.append(bin(int(args[0]))[2:].zfill(5))               # task id
        fields.append(bin(int(args[1]["frequency"]))[2:].zfill(8))  # freq
        fields.append(bin(int(args[1]["threshold"]))[2:].zfill(16)) # threshold
        fields.append(bin(int(args[1]["task_type"]))[2:].zfill(3))  # task_type

        if args[1]["task_type"] == 2:                               # calcular latência
            ip_int = int(ipaddress.IPv4Address(args[1]["destination"]))
            ip_bin = format(ip_int, '032b')

            fields.append(ip_bin)                                   # destino para usar no ping
        elif args[1]["task_type"] == 3:                             # calcular largura de banda + jitter
            ip_src = int(ipaddress.IPv4Address(args[1]["source"]))
            ip_src_bin = format(ip_src, '032b')
            ip_dst = int(ipaddress.IPv4Address(args[1]["destination"]))
            ip_dst_bin = format(ip_dst, '032b')
            
            fields.append(ip_src_bin)                               # ip do servidor para usar no iperf
            fields.append(ip_dst_bin)                               # ip do cliente para usar no iperf         
        elif args[1]["task_type"] == 4:                             # interface a monitorizar
            interf = args[1]["interface_name"].ljust(10)
            interface : str = ''.join(format(ord(character), '08b') for character in interf) 
            fields.append(interface)                                

        print(args)
        print(fields)
    else:
        print(f"isto não é uma task {fields[1]}")

    agent_data.acquire_lock() # necessário para que outras threads não escrevam no mesmo nrº de sequência
    fields[2] = bin(agent_data.get_seq())[2:].zfill(16)             # número de sequência

    message : str = ''
    for field in fields:
        message += field

    print(f"o tipo de message é {type(message)}")
    message_bytes = int(message, 2).to_bytes(len(message) // 8, byteorder='big')
    
    if message_type == Message_type.TASK.value:
        agent_data.inc_seq(len(message_bytes))
    
    agent_data.release_lock()
    # Enviar mensagem pelo socket UDP
    s.sendto(message_bytes, address)

    
def process(message : tuple, s : socket.socket, agent_list : dict): # mensagem ser um array é funcionamennto básico do socket
    fields : list = parser.parse(message[0]) #[agent_id, message_type, seq]

    print(fields) # exemplo - [20, 0, 0]
    print(f"O enum é {Message_type.REGISTER.value} e o inteiro é {fields[1]}")
    if fields[1] == Message_type.REGISTER.value:
        print(f"registo recebido do agente {fields[0]}")
        agent_list[fields[0]] = Shared() # cria um objeto partilhado
        agent_list[fields[0]].inc_seq(len(message[0])) # aumenta o seq
        send(s, message[1], fields[0], Message_type.ACK.value, agent_list[fields[0]]) # envia ack de volta (message type 1)
        
        # a partir de aqui, vai-se tratar de enviar tarefas, o que faz parte do registo
        address : tuple = message[1]
        tasks : dict = parser.parse_tasks(str(fields[0]))

        for key, value in tasks.items():
            threading.Thread(target=send, args=(s, address, fields[0], Message_type.TASK.value, agent_list[fields[0]], key, value)).start()
    elif fields[1] == Message_type.METRIC.value:
        print(f"RECEBI MÉTRICAS com {fields}")
    else:
        print("não é registo")
        
    

def start(address: str, port: int): 
    agent_list : dict = dict()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # criar socket
    #AF_INET diz que é ipv4
    #SOCK_DGRAM diz que é UDP
    s.bind((address, port)) # associei o socket a um par endereço-porta
    
    while True:  
        message = s.recvfrom(1024) # buffer de 1024 bytes para receber mensagem (array de bytes)
        #print("recebi uma mensagem UDP!")
        threading.Thread(target=process, args=(message, s, agent_list)).start()

    s.close() 