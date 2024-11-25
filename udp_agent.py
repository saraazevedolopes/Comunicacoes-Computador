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
from datetime import datetime
import sys
import logger
import re

# Envia uma mensagem binária 
def send(s : socket.socket, address : tuple, agent_id : int, message_type : int, shared_server : Shared, retransmission : bool, *args) -> int: # args tem um id e um dicionário
    fields : list = list()
    fields.append(bin(agent_id)[2:].zfill(5))     # id agente
    fields.append(bin(message_type)[2:].zfill(3)) # message type
    fields.append(0)                              # número de sequência

    # Adquirir lock necessário para que outras threads não escrevam no mesmo nrº de sequência
    shared_server.acquire_lock() 
    
    # Se não for retransmissão
    if not retransmission:
        seq = shared_server.get_seq()

    # Retransmissão
    else:
        logger.log(f"A retransmitir o pacote de seq={args[0]}")
        seq = args[0]

    fields[2] = bin(seq)[2:].zfill(16)            # número de sequência

    # Metric
    if message_type == 3:
        fields.append(bin(args[0])[2:].zfill(5))
        fields.append(bin(args[1])[2:].zfill(3))
        
        # CPU
        if args[1] == 0:
            fields.append(bin(args[2])[2:].zfill(16))
        
        # RAM
        elif args[1] == 1:
            fields.append(bin(args[2])[2:].zfill(16))

        # Latência
        elif args[1] == 2:
            fields.append(bin(args[2])[2:].zfill(16))
            
        # Throughput 
        elif args[1] == 3:
            fields.append(bin(args[2])[2:].zfill(16)) # Throughput
            fields.append(format(ord(args[3]), '08b'))  # Unidade do throughput
            fields.append(bin(args[4])[2:].zfill(16)) # Jitter
            fields.append(bin(args[5])[2:].zfill(8))  # Losses 
        
        # Interfaces
        else:
            fields.append(bin(args[2])[2:].zfill(8)) # Estado da interface
            

    # Juntar todos os campos, pdu
    message : str = ''
    for field in fields:
        message += field

    # Conversão para bytes
    message_bytes = int(message, 2).to_bytes(len(message) // 8, byteorder='big')

    # Se não é uma retransmissão, nem um Ack, então aumenta o nº seq
    if (not retransmission) and (message_type != 1): 
        shared_server.inc_seq(len(message_bytes))

    shared_server.release_lock()

    # Enviar mensagem pelo socket UDP
    s.sendto(message_bytes, address)

    return seq

# Processa mensagens recebidas pelo servidor, interpretando-as e executando as ações necessárias  
def process(s : socket.socket, message : tuple, shared_server : Shared):
    fields : list = parser.parse(message[0])
    logger.log(f"Os campos são {fields}")

    agent_id, message_type = fields[:2]
    
    # Ack
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
        #TER CUIDADO COM RETRANSMISSÕES
        try:
            shared_server.acquire_lock()
            #logger.log(f"O tamanho do pacote recebido é {len(message[0])}")
            shared_server.inc_seq(len(message[0]))
            #logger.log(f"o seq neste momento é {shared_server.get_seq()}")   
            shared_server.set_received_packet(True)
        finally:
            shared_server.release_lock()

    if message_type == 2 and (fields[6] in [0,1,2,3,4]): # 0 CPU, 2 latência, 4 interface TIRARRRRRRRRRRRRRRRRRRRRRRRRR TODO
        logger.log(fields)
        run_task(s, message[1], shared_server, fields)
          
# Executa uma tarefa recebida      
def run_task(s : socket.socket, address : tuple, shared_server : Shared, fields : list):
    logger.log(f"args: {fields}")
    
    agent_id = fields[0]
    task_id = fields[3]
    frequency = fields[4]
    threshold = fields[5]
    task_type = fields[6]

    # CPU
    if task_type == 0:
        logger.log("Isto é um pedido de CPU")
        while True:
            cpu_usage = psutil.cpu_percent()
            logger.log(f"[CPU Utilização]: {cpu_usage}")
            logger.log(f"[CPU Timestamp] {datetime.now()}")
            threading.Thread(target=send, args=(s, address, agent_id, 3, shared_server, False, task_id, task_type, int(round(cpu_usage,0)))).start() 
            time.sleep(frequency)
            send(s, address, agent_id, 3, shared_server, False, task_id, task_type, int(round(cpu_usage, 0)))
    
    # RAM
    elif task_type == 1:
        while True:
            ram_usage = psutil.virtual_memory()
            logger.log(f"[RAM Utilização]: {ram_usage.percent}%")
            threading.Thread(target=send, args=(s, address, agent_id, 3, shared_server, False, task_id, task_type, int(round(ram_usage.percent,0)))).start() 
            time.sleep(frequency)
    
    # Latência
    elif task_type == 2:
        destination = fields[7]
        
        while True:
            responses = subprocess.run(
                ["ping", "-c", "4", destination],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            result = 0
            for line in responses.stdout.splitlines():
                if "min/avg/max" in line or "rtt min/avg/max" in line: # Adapta dependendo do sistema
                    logger.log(f"[LATÊNCIA resumo tempo de resposta]: {line}")
                    result = int(round(float(line.split("/")[4]), 0))

            threading.Thread(target=send, args=(s, address, agent_id, 3, shared_server, False, task_id, task_type, result)).start() 
            time.sleep(frequency)
    
    # Throughput 
    elif task_type == 3:
        server_address = fields[8]
        if fields[7] == 0:
            is_server = False
            command = ["iperf3", "-u", "-c", server_address]
        else:
            is_server = True
            command = ["iperf3", "--one-off", "-s", "-B", server_address]
            print(f"SOU O SERVIDOR IPERF")

        while True:  
            responses = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
            )
            
            print("TERMINEI O IPERF")
            if not responses.stderr:
                if is_server:
                    line = responses.stdout.splitlines()[-1]
                    print(f"{line}")
                else:
                    line = responses.stdout.splitlines()[-3]
                    print(f"{line}")

                campos = line.split(" ")
                numbers = re.findall(r'-?\d+\.?\d*', line)
                
                throughput = int(round(float(numbers[4]),0))
                jitter = int(round(float(numbers[5]),0))
                #jitter = int(round(numbers[5],0))
                losses = int(round(float(numbers[-1]),0)) 

                if "Kbits/sec" in line: # Bitrate pode ter unidades diferentes
                    unit = "K"
                elif "Mbits/sec" in line:
                    unit = "M"
                else:
                    unit = "G"
                
                print(f"Última linha: {responses.stdout.splitlines()[-1]}")
                    
                total_throughput = round(throughput,0)
                total_jitter = round(jitter,0)
                total_losses = round(losses,0)

                print(f"Throughput: {total_throughput} {unit}")
               
                print(f"média throughput: {total_throughput} {unit}bits/s\n"
                f"média jitter: {total_jitter}\n"
                f"média loss: {total_losses}\n")        
                threading.Thread(target=send, args=(s, address, agent_id, 3, shared_server, False, task_id, task_type, throughput, unit, jitter, losses)).start() 
            else:
                print(f"ERROS: {responses.stderr}")
            time.sleep(frequency)
            
    
    # Interfaces
    elif task_type == 4:
        interface_bits = fields[7]
        # Descodificar o nome da interface (transformar de binário para string)
        interface_name = ''.join(
            chr(int(interface_bits[i:i+8], 2)) for i in range(0, len(interface_bits), 8)
        ).strip()

        while True:
            try:
                # Obter estado da interface
                net_stats = psutil.net_if_stats()

                if interface_name in net_stats:
                    # Verificar se a interface está "up"
                    is_up = net_stats[interface_name].isup
                    status_print = "UP" if is_up else "DOWN"

                    # Estado da interface
                    logger.log(f"[INTERFACE STATUS]: {interface_name} está {status_print}")
                    
                    status = 1 if is_up else 0
                    # Enviar o estado ao servidor
                    send(s, address, agent_id, 3, shared_server, False, task_id, task_type, status)
                else:
                    logger.log(f"[ERRO INTERFACE]: {interface_name} não encontrada.")
                    break
            except Exception as e:
                logger.log(f"[ERRO MONITORIZAÇÃO INTERFACE]: {e}")
            time.sleep(frequency)


        """
        while True:
            for iface in interfaces:
                iface_details = netifaces.ifaddresses(iface)
                logger.log(f"A interface {iface} tem esta informação: {iface_details}")
            time.sleep(frequency)
        """

def register(s : socket.socket, address: str, port: int, agent_name : str, shared_server : Shared):
    success = False
    seq = send(s, (address, port), int(agent_name), 0, shared_server, False)
    while not success:
        success = shared_server.acquire_received_condition(seq)
        if not success:
            logger.log(f"TIMEOUT no pacote de seq = {seq}")
            send(s, (address, port), int(agent_name), 0, shared_server, True, seq)
        else:
            logger.log(f"RECEBI O ACK CORRETAMENTE para seq = {seq}")
        
    #message = s.recvfrom(1024) # TODO era melhor ter um while para saber até onde ler, mas por agora assumir tamanho fixo
    
    # Ver número do ACK
    #process(s, message, shared_server)

# Verifica periodicamente se há ACKs recebidos e notifica o estado partilhado
# TODO 3 ack cumulativo
def ack_monitor(s : socket.socket, address : tuple, agent_id : int, shared_server : Shared):
    while True:
        time.sleep(1)
        shared_server.notify_received_condition()
        if shared_server.get_received_ack():
            logger.log("Houve ACK recebido")
            shared_server.set_received_ack(False)
        
       
# Envia ACKs de volta ao servidor ao detectar pacotes recebidos
def ack_sender(s : socket.socket, address : tuple, agent_id : int, shared_server : Shared):
    while True:
        time.sleep(1)
        if shared_server.get_received_packet():
            logger.log(f"Houve pacotes recebidos e o nº de seq está a {shared_server.get_seq()}")
            send(s, address, agent_id, 1, shared_server, False)
            shared_server.set_received_packet(False)

def start(address: str, port: int, agent_name : str): 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    shared_server = Shared()
    threading.Thread(target=register, args=(s, address, port, agent_name, shared_server)).start()
    threading.Thread(target=ack_monitor, args=(s, (address, port), int(agent_name), shared_server)).start()
    threading.Thread(target=ack_sender, args=(s, (address, port), int(agent_name), shared_server)).start()
    
    while True:  
        message = s.recvfrom(1024) 
        logger.log("recebi uma mensagem UDP!")

        # 1 thread por task
        threading.Thread(target=process, args=(s, message, shared_server)).start() 

    s.close()