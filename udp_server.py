import socket
import json
import parser
from Shared import Shared
import threading

# envia uma tarefa serializada em bytes para um agente especificado através do socket UDP
def send(s : socket.socket, address : tuple, agent_id : int, message_type : int, *args): #args é uma lista de 0 ou mais elementos, ack -> lista sem elementos, envio task -> n elementos
    #transformar isto em lista para termos a possibilidade de ter um número variável de campos
    agent_id = bin(agent_id)[2:].zfill(5)
    message_type = bin(message_type)[2:].zfill(3)

    message = agent_id + message_type 
    
    message_bytes = int(message, 2).to_bytes(len(message) // 8, byteorder='big')
    # Enviar mensagem pelo socket UDP
    s.sendto(message_bytes, address)


# recebe uma mensagem UDP, extrai os campos
def process(message : tuple, s : socket.socket, agent_list : dict): # mensagem ser um array é funcionamennto básico do socket
    fields : list = parser.parse(message[0]) # [agent_id, message_type, seq]

    print(fields)
    if fields[1] == 0:
        print(f"registo recebido do agente {fields[0]}")
        agent_list[fields[0]] = Shared() # cria um objeto partilhado
        send(s, message[1], fields[0], 1) # envia ack de volta (message type 1)
    else:
        print("não é registo")
        
        
    address : tuple = message[1]
    #tasks : dict = parser.parse_tasks(agent_name)

    #for key, value in tasks.items():
    #    threading.Thread(target=send, args=(agent_name, address, shared, key, value, s)).start()


def start(address: str, port: int): 
    agent_list : dict = dict()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # criar socket
    #AF_INET diz que é ipv4
    #SOCK_DGRAM diz que é UDP
    s.bind((address, port)) # associei o socket a um par endereço-porta
    
    while True:  
        message = s.recvfrom(1024) # buffer de 1024 bytes para receber mensagem (array de bytes)
        print("recebi uma mensagem UDP!")
        threading.Thread(target=process, args=(message, s, agent_list)).start()

    s.close() 