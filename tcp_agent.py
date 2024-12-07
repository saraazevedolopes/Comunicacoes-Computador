import socket
import time
from queue import Queue

def send(s : socket.socket, alert):
    fields : list = list()
    fields.append(bin(alert[0])[2:].zfill(5))      # id agente
    fields.append(bin(alert[1])[2:].zfill(3))      # task type
    fields.append(bin(alert[2])[2:].zfill(8))      # task ID
    
    # CPU, RAM, Latência
    if alert[1] in [0,1,2]:
        fields.append(bin(alert[3])[2:].zfill(16))      #métrica medida
        fields.append(bin(0)[2:].zfill(32))             #padding para todos os pacotes terem 8 bytes
    # Throughput
    elif alert[1] == 3:
        fields.append(bin(alert[3][0])[2:].zfill(16))   # Throughput
        fields.append(format(ord(alert[3][1]), '08b'))  # Unidade do throughput
        fields.append(bin(alert[3][2])[2:].zfill(16))   # Jitter
        fields.append(bin(alert[3][3])[2:].zfill(8))    # Losses 
    # Interfaces
    else:
        fields.append(bin(alert[3])[2:].zfill(8)) # Estado da interface
        fields.append(bin(0)[2:].zfill(40))       # Padding
           
    # Juntar todos os campos, pdu
    message : str = ''
    for field in fields:
        message += field

    # Conversão para bytes
    message_bytes = int(message, 2).to_bytes(len(message) // 8, byteorder='big')

    # Enviar mensagem pelo socket UDP
    s.sendall(message_bytes)    

def start(address: str, port: int, alert_queue : Queue): 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.connect((address, port)) 

    while True:
        while not alert_queue.empty():
            send(s,alert_queue.get())
        time.sleep(0.1)
    