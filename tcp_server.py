import socket
import parser
import threading

def agent_connection(connection: socket.socket):
    while True:
        mensagem = connection.recv(1024) # buffer de 1024 bytes para receber mensagem (array de bytes)

        threading.Thread(target=parser.parse_tcp, args=(mensagem,)).start()

def start(address: str, port: int): 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # criar socket para receber syn
    #AF_INET diz que é ipv4
    #SOCK_STREAM diz que é TCP
    s.bind((address, port)) # associamos o socket a um par endereço-porta, podia ser a mesma porta

    s.listen(5) # ficar à escuta de pedidos de ligação (SYN), 5 - número de falhas até rejeitar a ligação, proteger de DDOS
    print("Sucesso no bind, TCP")
    
    while True: 
        connection, agent_address = s.accept() # quando aceito uma ligação de um endereço, agent_address, recebo um socket (socket dentro de um socket para comunicação) 
        threading.Thread(target=agent_connection, args=(connection,)).start()
        
        
    

