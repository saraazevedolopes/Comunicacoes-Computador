import socket
import json
import struct # pega numa estrutura de dados e passa para bytes e vice-versa
import parser
from Shared import Shared
import threading

#campos do cabeçalho:
#ID
#número de sequência (server)
#ACK (número de sequência que confirmamos do agente)
#nome da tarefa
#parâmetros do comando
#frequência
#métricas do dispositivo
#métricas de link
#condições do AlertFlow

# Formato do cabeçalho do protocolo UDP 
# "server", seq, ack, task_name, task_contents 
# string de 6 bytes, short int de 2 bytes, short int de 2 bytes, string de 15 bytes, string de 25 bytes
HEADER_FORMAT = "6s H H 15s 25s"

# envia uma tarefa serializada em bytes para um agente especificado através do socket UDP
def send(agent_name : str, address : tuple, shared : Shared, task_name : str, task_contents : dict, s : socket.socket):
    seq : int = shared.get_seq()
    ack : int = shared.get_ack()

    # ???? default ?????
    server_str = "server".encode('ascii').ljust(6, b'\x00')  # 6 bytes com padding de zero
    
    # Convertendo nome e conteúdo da tarefa para bytes, limitando o tamanho e preenchendo com zero 
    task_name_bytes = task_name.encode('ascii')[:15].ljust(15, b'\x00') 
    task_contents_str = json.dumps(task_contents)[:25]
    task_contents_bytes = task_contents_str.encode('ascii').ljust(25, b'\x00')
    
    header = struct.pack(HEADER_FORMAT, server_str, seq, ack, task_name_bytes, task_contents_bytes)
    
    # Enviar mensagem pelo socket UDP
    s.sendto(header, address)


# recebe uma mensagem UDP, extrai o nome do agente e endereço, e inicia threads para enviar tarefas ao agente
def process(message : tuple, s : socket.socket):
    #TODO: validar registo
    print(message[0].decode()) # 0 - array de bytes que contém a mensagem
    print(message[1]) # 1 - tuplo, endereço-porta do agente

    shared : Shared = Shared(message[0]) 

    agent_name : str = message[0].decode()
    address : tuple = message[1]
    tasks : dict = parser.parse_tasks(agent_name)

    for key,value in tasks.items():
        threading.Thread(target=send, args=(agent_name,address,shared,key,value,s)).start() # cria threads para cada task

def start(address: str, port: int): 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # criar socket
    #AF_INET diz que é ipv4
    #SOCK_DGRAM diz que é UDP
    s.bind((address, port)) # associei o socket a um par endereço-porta
    
    while True:  
        message = s.recvfrom(1024) # buffer de 1024 bytes para receber mensagem (array de bytes)
        print("recebi uma mensagem UDP!")
        threading.Thread(target=process, args=(message, s)).start()

    s.close() # ya