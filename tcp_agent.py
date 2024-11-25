import socket

def start(address: str, port: int): 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # criar socket para receber syn
    #AF_INET diz que é ipv4
    #SOCK_STREAM diz que é TCP
    #s.bind(("10.0.0.2", port)) # não precisa de bind, porque não me importo que seja aleatório
    
    s.connect((address, port)) 

    mensagem = s.send("mensagem TCP".encode()) # buffer de 1024 bytes para enviar mensagem (array de bytes)
    