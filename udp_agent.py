import socket
import parser
import threading
import time
from Shared import Shared
from pythonping import ping
import psutil
import subprocess
import os
import logger
import re
from queue import Queue
from Message_type import Message_type
import signal
import logging


# Envia uma mensagem binária       
def send(s : socket.socket, address : tuple, agent_id : int, message_type : int, shared_server : Shared, retransmission : bool, *args) -> int: # args tem um id e um dicionário
    fields : list = list()
    fields.append(bin(agent_id)[2:].zfill(5))     # id agente
    fields.append(bin(message_type)[2:].zfill(3)) # message type
    fields.append(0)                              # número de sequência
    seq = 0

    if message_type != Message_type.END.value:
        inc = 0
        # Adquirir lock necessário para que outras threads não escrevam no mesmo nrº de sequência
        shared_server.acquire_lock() 
        
        # Se não for retransmissão
        if not retransmission and message_type != 1:
            seq = shared_server.get_seq()

        # Retransmissão
        else:
            seq = args[0]
            inc = 1 

        fields[2] = bin(seq)[2:].zfill(16)            # número de sequência

        # Metric
        if message_type == 3:
            fields.append(bin(args[0+inc])[2:].zfill(5))
            fields.append(bin(args[1+inc])[2:].zfill(3))
            
            # CPU
            if args[1+inc] == 0:
                fields.append(bin(args[2+inc])[2:].zfill(16))
            
            # RAM
            elif args[1+inc] == 1:
                fields.append(bin(args[2+inc])[2:].zfill(16))

            # Latência
            elif args[1+inc] == 2:
                fields.append(bin(args[2+inc])[2:].zfill(16))
                
            # Throughput 
            elif args[1+inc] == 3:
                fields.append(bin(args[2+inc])[2:].zfill(16)) # Throughput
                fields.append(format(ord(args[3+inc]), '08b'))  # Unidade do throughput
                fields.append(bin(args[4+inc])[2:].zfill(16)) # Jitter
                fields.append(bin(args[5+inc])[2:].zfill(8))  # Losses 
            
            # Interfaces
            else:
                fields.append(bin(args[2+inc])[2:].zfill(8)) # Estado da interface
    else:
        fields[2] = bin(0)[2:].zfill(16)        

    # Juntar todos os campos, pdu
    message : str = ''
    for field in fields:
        message += field

    # Conversão para bytes
    message_bytes = int(message, 2).to_bytes(len(message) // 8, byteorder='big')

    # Se não é uma retransmissão, nem um Ack, então aumenta o nº seq
    if (not retransmission) and (message_type != Message_type.ACK.value) and (message_type != Message_type.END.value): 
        shared_server.inc_seq(len(message_bytes))

    if message_type != Message_type.END.value:
        shared_server.release_lock()

    # Enviar mensagem pelo socket UDP
    s.sendto(message_bytes, address)

    return seq,message_bytes

# Processa mensagens recebidas pelo servidor, interpretando-as e executando as ações necessárias  
def process(s : socket.socket, message : tuple, shared_server : Shared, alert_queue : Queue, agent_logger):
    fields : list = parser.parse(message[0], False, agent_logger)
    agent_id, message_type = fields[:2]
    
    # Ack
    if fields[1] == Message_type.ACK.value:
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
    elif fields[1] == Message_type.TASK.value:
        shared_server.acquire_lock()

        if shared_server.received_seq(fields[2]):
            shared_server.release_lock()
            return
        else:
            shared_server.add_packet(fields[2])
            expected_seq = shared_server.get_seq() 
        shared_server.release_lock()
        while fields[2] >= expected_seq:
            if fields[2] == expected_seq:    
                shared_server.acquire_lock()
                shared_server.inc_seq(len(message[0]))
                shared_server.release_lock()
                shared_server.set_received_packet(True)
                break
            time.sleep(0.1)
            shared_server.acquire_lock()
            expected_seq = shared_server.get_seq() 
            shared_server.release_lock()
        else:
            return
    elif fields[1] == Message_type.END.value:
        agent_logger.info(f"Received END packet from the server, shutting down.\n\n")
        
        send(s, message[1], fields[0], 4, shared_server, False)
        
        result = subprocess.run(['pgrep', '-f', 'agent.py'], stdout=subprocess.PIPE, text=True)
        pids = result.stdout.strip().split('\n')

        for pid in pids:
            pid = int(pid)
            os.kill(pid, signal.SIGINT)
                
    if message_type == 2:
        run_task(s, message[1], shared_server, fields, alert_queue, agent_logger)
          
# Executa uma tarefa recebida      
def run_task(s : socket.socket, address : tuple, shared_server : Shared, fields : list, alert_queue : Queue, agent_logger):
    agent_id = fields[0]
    task_id = fields[3]
    frequency = fields[5]
    threshold = fields[6]
    task_type = fields[4]
    consecutive_fails = 0

    time.sleep(5)
    # CPU
    if task_type == 0:
        while True:
            cpu_usage = psutil.cpu_percent()
            if cpu_usage > threshold:
                alert_queue.put([agent_id, task_id, task_type, int(round(cpu_usage,0))])
                agent_logger.warning(f"CPU threshold surpassed for task {task_id}, measured {cpu_usage}% with threshold {threshold}%")
                consecutive_fails += 1
            else:
                agent_logger.info(f"CPU task {task_id} measured cpu usage of {cpu_usage}%")
                threading.Thread(target=schedule_send, args=(s, agent_logger, address[0], address[1], agent_id, 3, shared_server, task_id, task_type, int(round(cpu_usage,0)))).start() 
                consecutive_fails = 0

            if consecutive_fails == 3:
                    agent_logger.critical(f"3 consecutive fails on CPU task {task_id}")
                    return
            time.sleep(frequency)
            
    # RAM
    elif task_type == 1:
        while True:
            ram_usage = psutil.virtual_memory()
            
            if ram_usage.percent > threshold:
                alert_queue.put([agent_id, task_id, task_type, int(round(ram_usage.percent,0))])
                agent_logger.warning(f"RAM threshold surpassed for task {task_id}, measured {ram_usage.percent}% with threshold {threshold}%")
                consecutive_fails += 1
            else:
                agent_logger.info(f"RAM task {task_id} measured cpu usage of {ram_usage.percent}%")
                threading.Thread(target=schedule_send, args=(s,agent_logger, address[0], address[1], agent_id, 3, shared_server, task_id, task_type, int(round(ram_usage.percent,0)))).start() 
                consecutive_fails = 0
            if consecutive_fails == 3:
                    agent_logger.critical(f"3 consecutive fails on RAM task {task_id}")
                    return
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
                    #logger.log(f"[LATÊNCIA resumo tempo de resposta]: {line}")
                    result = int(round(float(line.split("/")[4]), 0))
            if result > threshold:
                alert_queue.put([agent_id, task_id, task_type, result])
                agent_logger.warning(f"Threshold surpassed for LATENCY task {task_id}, measured {result}ms with threshold {threshold}ms")
                consecutive_fails += 1    
            else:
                agent_logger.info(f"LATENCY task {task_id} measured a latency of {result}ms to {destination}")
                threading.Thread(target=schedule_send, args=(s, agent_logger,address[0], address[1], agent_id, 3, shared_server, task_id, task_type, result)).start() 
                consecutive_fails = 0
            if consecutive_fails == 3:
                agent_logger.critical(f"3 consecutive fails on LATENCY task {task_id}")
                return
            time.sleep(frequency)
    
    # Throughput 
    elif task_type == 3:
        server_address = fields[8]
        if fields[7] == 0:
            is_server = False
            command = ["iperf3", "-u", "-c", server_address, "-b", "5M"]
        else:
            frequency-=5
            is_server = True
            command = ["iperf3", "--one-off", "-s", "-B", server_address]
            
        while True:  
            responses = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
            )
            
            if not responses.stderr:
                if is_server:
                    line = responses.stdout.splitlines()[-1]
                else:
                    line = responses.stdout.splitlines()[-3]

                numbers = re.findall(r'-?\d+\.?\d*', line)
                
                throughput = int(round(float(numbers[4]),0))
                jitter = int(round(float(numbers[5]),0))
                losses = int(round(float(numbers[-1]),0)) 

                if "Kbits/sec" in line: # Bitrate pode ter unidades diferentes
                    unit = "K"
                elif "Mbits/sec" in line:
                    unit = "M"
                else:
                    unit = "G"
                
                total_throughput = round(throughput,0)
                total_jitter = round(jitter,0)
                total_losses = round(losses,0)

                if unit == "K" or total_throughput < threshold[0] or total_jitter > threshold[1] or total_losses > threshold[2]:
                    alert_queue.put([agent_id, task_id, task_type, [total_throughput,unit,total_jitter,total_losses]])
                    if unit =="K" or total_throughput < threshold[0]:
                        agent_logger.warning(f"Throughput threshold surpassed for IPERF task {task_id}, measured {total_throughput}{unit}bps with threshold {threshold[0]}Mbps")
                    elif total_jitter > threshold[1]:
                        agent_logger.warning(f"Jitter threshold surpassed for IPERF task {task_id}, measured {total_jitter}ms with threshold {threshold[0]}ms")
                    else:
                        agent_logger.warning(f"Loss threshold surpassed for IPERF task {task_id}, measured {total_losses}% with threshold {threshold[0]}%")
                    
                    consecutive_fails+=1
                else:   
                    agent_logger.info(f"IPERF task {task_id} measured Throughput={total_throughput}{unit}bps, Jitter={total_jitter}ms, Loss={total_losses}%")
                    threading.Thread(target=schedule_send, args=(s, agent_logger,address[0], address[1], agent_id, 3, shared_server, task_id, task_type, throughput, unit, jitter, losses)).start() 
                    consecutive_fails=0       
            else:
                alert_queue.put([agent_id, task_id, task_type, [0,"K",0,100]])
                agent_logger.warning(f"IPERF task {task_id} failed without connectivity")
                consecutive_fails+=1
            if consecutive_fails == 3:
                    agent_logger.critical(f"3 consecutive fails on IPERF task {task_id}")
                    return
            time.sleep(frequency)        
    
    # Interfaces
    elif task_type == 4:
        interface_name = fields[7]

        while True:
            try:
                # Obter estado da interface
                net_stats = psutil.net_if_stats()

                if interface_name in net_stats:
                    # Verificar se a interface está "up"
                    is_up = net_stats[interface_name].isup
                    
                    status = 1 if is_up else 0

                    if status == 0:
                        alert_queue.put([agent_id, task_id, task_type, status])
                        agent_logger.warning(f"INTERFACE task {task_id} failed, {interface_name} is DOWN.")
                        consecutive_fails += 1
                    else:
                        threading.Thread(target=schedule_send, args=(s,agent_logger,address[0], address[1], agent_id, 3, shared_server, task_id, task_type, status)).start() 
                        consecutive_fails = 0   
                    # Enviar o estado ao servidor
                    if consecutive_fails == 3:
                            agent_logger.critical(f"3 consecutive fails on INTERFACE task {task_id}")
                            return
                else:
                    #logger.log(f"[ERRO INTERFACE]: {interface_name} não encontrada.")
                    break
            except Exception as e:
                pass
                # logger.log(f"[ERRO MONITORIZAÇÃO INTERFACE]: {e}")
            time.sleep(frequency)

def schedule_send(s : socket.socket, agent_logger, address: str, port: int, agent_name : str, message_type : int, shared_server : Shared, *args):
    success = False
    
    seq, packet = send(s, (address, port), int(agent_name), message_type, shared_server, False, *args)
    agent_logger.info(f"SENDING SEQ={seq}, MESSAGE_TYPE={message_type}, LENGTH={len(packet)} bytes")
    while not success:
        success = shared_server.acquire_received_condition(seq, agent_logger)
        if not success:
            #agent_logger.warning(f"TIMEOUT occured in packet with SEQ= {seq}")
            s.sendto(packet, (address,port))

def schedule_end(address: str, port: int, agent_name : str):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1)
    success = False
    counter = 0
    seq, pacote = send(s, (address, port), int(agent_name), Message_type.END.value, None, False)
    while not success and counter < 3:
        try:
            message = s.recv(1024)
            success = True
        except socket.timeout:
            counter+=1
            s.sendto(pacote, (address,port))
            

# Verifica periodicamente se há ACKs recebidos e notifica o estado partilhado
def ack_monitor(shared_server : Shared):
    while True:
        time.sleep(.5)
        shared_server.notify_received_condition()
        if shared_server.get_received_ack():
            shared_server.set_received_ack(False)
              
# Envia ACKs de volta ao servidor ao detectar pacotes recebidos
def ack_sender(s : socket.socket, address : tuple, agent_id : int, shared_server : Shared, agent_logger):
    while True:
        time.sleep(0.1)
        shared_server.acquire_lock()
        if shared_server.get_received_packet():
            ack_seq = shared_server.get_seq()
            agent_logger.debug(f"SENDING ACK SEQ={ack_seq}")
            threading.Thread(target=send, args=(s, address, agent_id, 1, shared_server, False, ack_seq)).start()
            shared_server.set_received_packet(False)
        shared_server.release_lock()

def start(s : socket.socket, address: str, port: int, agent_name : str, alert_queue : Queue, agent_logger):
    shared_server = Shared()
    agent_logger.info(f"Agent{agent_name} started.")

    threading.Thread(target=schedule_send, args=(s, agent_logger,address, port, agent_name, 0, shared_server)).start()
    threading.Thread(target=ack_monitor, args=(shared_server,)).start()
    threading.Thread(target=ack_sender, args=(s, (address, port), int(agent_name), shared_server, agent_logger)).start()
    
    while True:  
        message = s.recvfrom(1024) 

        # 1 thread por segmento recebido
        threading.Thread(target=process, args=(s, message, shared_server, alert_queue, agent_logger)).start() 

    s.close()