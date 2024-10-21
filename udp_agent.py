import socket

def start(address: str, port: int): 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 

    #s.bind((address, port)) não precisamos de ter porta e endereço fixo
    #sendto, 2 argumentos. 1º array de bytes a enviar, 2º para onde enviar
    s.sendto("mensagem UDP".encode(), (address, port)) # endecode: pega na string e converte para um array de bytes

