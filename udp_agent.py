import socket
import parser
import threading
import time
from Shared import Shared
from pythonping import ping
import psutil
import subprocess
import netifaces
import struct

def send(s : socket.socket, address : tuple, agent_id : int, message_type : int, shared_server : Shared, retransmission : bool, *args) -> int: # args tem um id e um dicionário
    fields : list = list()
    fields.append(bin(agent_id)[2:].zfill(5)) # id agente
    fields.append(bin(message_type)[2:].zfill(3)) # message type
    fields.append(0) # arbitrário, este campo depois será preenchido com o número de sequência

    shared_server.acquire_lock() # necessário para que outras threads não escrevam no mesmo nrº de sequência
    if not retransmission:
        seq = shared_server.get_seq()
    else:
        print(f"A retransmitir o pacote de seq={args[0]}")
        seq = args[0]

    fields[2] = bin(seq)[2:].zfill(8) # número de sequência

    if message_type == 3:
        fields.append(bin(args[0])[2:].zfill(5))
        fields.append(bin(args[1])[2:].zfill(3))
        if args[1] == 0:
            pass
        elif args[1] == 1:
            pass
        elif args[1] == 2:
            print("A enviar métrica de latência")
            packed = struct.pack('!d', args[1])
            binary = ''.join(f'{byte:08b}' for byte in packed)
            fields.append(binary[2:])
        elif args[1] == 3:
            pass
        else:
            pass
    message : str = ''

    for field in fields:
        message += field

    message_bytes = int(message, 2).to_bytes(len(message) // 8, byteorder='big')

    if (not retransmission) and (message_type != 1): # se não é uma retransmissão, nem um Ack, então aumenta o seq
        shared_server.inc_seq(len(message_bytes))

    shared_server.release_lock()
    # Enviar mensagem pelo socket UDP
    s.sendto(message_bytes, address)

    return seq

# só recebe tasks e acks do servidor
#Recebe uma mensagem UDP, desserializa o conteúdo de message[0] de bytes para um formato de dados utilizável 
#(como uma lista ou dicionário) usando parser.parse, e imprime o resultado.
def process(s : socket.socket, message : tuple, shared_server : Shared):
    fields : list = parser.parse(message[0])
    print(f"Os campos são {fields}")

    agent_id, message_type = fields[:2]
    if fields[1] == 1:
        try:
            shared_server.acquire_lock()
            if fields[2] > shared_server.get_ack():
                shared_server.set_ack(fields[2])
                shared_server.notify_received_condition()
            else:
                shared_server.inc_repeats()
            shared_server.set_received_ack(True)
        finally:
            shared_server.release_lock()
    else:
        try:
            shared_server.acquire_lock()
            #print(f"O tamanho do pacote recebido é {len(message[0])}")
            shared_server.inc_seq(len(message[0]))
            #print(f"o seq neste momento é {shared_server.get_seq()}")   
            shared_server.set_received_packet(True)
        finally:
            shared_server.release_lock()

    if len(fields) == 8:
        print(fields)
        run_task(s, message[1], shared_server, fields)
          
def run_task(s : socket.socket, address : tuple, shared_server : Shared, fields : list):
    print(f"args: {fields}")
    agent_id = fields[0]
    task_id = fields[3]
    frequency = fields[4]
    threshold = fields[5]
    task_type = fields[6]

    if task_type == 0:
        print("Isto é um pedido de CPU")
        while True:
            cpu_usage = psutil.cpu_percent()
            print(f"Utilização do CPU: {cpu_usage}")
            time.sleep(frequency)
    elif task_type == 1:
        print("Isto é um pedido de RAM")
        while True:
            ram_usage = psutil.virtual_memory()
            print(f"Utilização da RAM: {ram_usage}")
            time.sleep(frequency)
    elif task_type == 2:
        print("Isto é um pedido de latência")
        destination = fields[7]

        while True:
            responses = subprocess.run(
                ["ping", "-c", "4", destination],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            result = list()
            for line in responses.stdout.splitlines():
                if "bytes from" in line or "Reply from" in line:  # Verifica se a linha contém resposta válida
                    result.append(float(line.split(" ")[6][5:]))
                elif "min/avg/max" in line or "rtt min/avg/max" in line:  # Adapta dependendo do sistema
                    print("Resumo do tempo de resposta:", line)
            print(result)
            ms = round(sum(result)/len(result),0)
            print(f"resultado em int: {int(ms)}")
            threading.Thread(target=send, args=(s, address, agent_id, 3, shared_server, False, task_id, task_type, ms)).start() 
            
            #s : socket.socket, address : tuple, agent_id : int, message_type : int, shared_server : Shared, retransmission : bool, *args) -> int: # args tem um id e um dicionário
            #send()

            time.sleep(frequency)
    elif task_type == 3:
        print("Isto é um pedido de largura de banda")
    elif task_type == 4:
        print("Isto é um pedido de interface")

        while True:
            for iface in interfaces:
                iface_details = netifaces.ifaddresses(iface)
                print(f"A interface {iface} tem esta informação: {iface_details}")
            time.sleep(frequency)

def register(s : socket.socket, address: str, port: int, agent_name : str, shared_server : Shared):
    success = False
    seq = send(s, (address, port), int(agent_name), 0, shared_server, False)
    while not success:
        success = shared_server.acquire_received_condition(seq)
        if not success:
            print(f"TIMEOUT no pacote de seq = {seq}")
            send(s, (address, port), int(agent_name), 0, shared_server, True, seq)
        else:
            print(f"RECEBI O ACK CORRETAMENTE para seq = {seq}")
        
    #message = s.recvfrom(1024) # TODO era melhor ter um while para saber até onde ler, mas por agora assumir tamanho fixo
    
    # Ver número do ACK
    #process(s, message, shared_server)

# Verifica periodicamente se há ACKs recebidos e notifica o estado partilhado
def ack_monitor(s : socket.socket, address : tuple, agent_id : int, shared_server : Shared):
    while True:
        time.sleep(1)
        shared_server.notify_received_condition()
        if shared_server.get_received_ack():
            print("Houve ACK recebido")
            shared_server.set_received_ack(False)
        
       
# Envia ACKs de volta ao servidor ao detectar pacotes recebidos
def ack_sender(s : socket.socket, address : tuple, agent_id : int, shared_server : Shared):
    while True:
        time.sleep(1)
        if shared_server.get_received_packet():
            print(f"Houve pacotes recebidos e o numero de sequencia está a {shared_server.get_seq()}")
            send(s, address, agent_id, 1, shared_server, False)
            shared_server.set_received_packet(False)

def start(address: str, port: int, agent_name : str): 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    shared_server = Shared()
    threading.Thread(target=register, args=(s, address, port, agent_name, shared_server)).start()
    threading.Thread(target=ack_monitor, args=(s, (address, port), int(agent_name), shared_server)).start() #inicializa thread para controlar acks cumulativos
    threading.Thread(target=ack_sender, args=(s, (address, port), int(agent_name), shared_server)).start()
    
    while True:  
        message = s.recvfrom(1024) 
        print("recebi uma mensagem UDP!")
        threading.Thread(target=process, args=(s, message, shared_server)).start() # uma thread por task

    s.close() 
    