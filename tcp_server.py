import socket

def start(address: str, port: int): 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # criar socket para receber syn
    #AF_INET diz que é ipv4
    #SOCK_STREAM diz que é TCP
    s.bind((address, port)) # associei o socket a um par endereço-porta, podia ser a mesma porta

    s.listen(5) # ficar à escuta de pedidos de ligação (SYN), 5 - número de falhas até rejeitar a ligação, proteger de DDOS
    print("succeeded in opening")
    
    while True: 
        connection, agent_address = s.accept() # quando aceito uma ligação de um endereço, agent_address, recebo um socket (socket dentro de um socket para comunicação) 

        mensagem = connection.recv(1024) # buffer de 1024 bytes para receber mensagem (array de bytes)
        # recvfrom é bloqueante, precisamos de threads

        print(mensagem.decode())
        print(agent_address)
        
    
