import socket
import json

def start(address: str, port: int): 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # criar socket
    #AF_INET diz que é ipv4
    #SOCK_DGRAM diz que é UDP
    s.bind((address, port)) # associei o socket a um par endereço-porta
    mensagem = s.recvfrom(1024) # buffer de 1024 bytes para receber mensagem (array de bytes)
    
    print(mensagem[0].decode()) # 0 - array de bytes que contém a mensagem
    print(mensagem[1]) # 1 - tuplo, endereço-porta do agente

    with open("agent63.json", "r") as file_json: # with garante que há um close do open
        data = json.load(file_json)
        print(data)