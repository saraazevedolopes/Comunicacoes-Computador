import socket
import parser
import threading

#Recebe uma mensagem UDP, desserializa o conteúdo de message[0] de bytes para um formato de dados utilizável 
#(como uma lista ou dicionário) usando parser.parse, e imprime o resultado.
def process(s : socket.socket, message : bytes):
    fields : list = parser.parse(message[0])
    print(fields)

def register(s : socket.socket, address: str, port: int, agent_name : str):
    # Converter para binário com preenchimento
    agent_id = bin(int(agent_name))[2:].zfill(5)  # 5 bits
    message_type = bin(0)[2:].zfill(3)            # 3 bits, está a 0, porque é registo
    seq = bin(0)[2:].zfill(8)                     # 8 bits, está a 0, porque é registo
    
    # Concatenar todos os binários
    message = agent_id + message_type + seq 

    # Converter a string binária para um número inteiro e depois para bytes
    message_bytes = int(message, 2).to_bytes(len(message) // 8, byteorder='big')

    print(f"Mensagem binária enviada: {message}")
    print(f"Bytes enviados: {message_bytes}")

    # Enviar a mensagem concatenada no socket
    s.sendto(message_bytes, (address, port))

    message = s.recvfrom(1024) # TODO era melhor ter um while para saber até onde ler, mas por agora assumir tamanho fixo
    print(f"Recebi resposta com {message}, atualmente é um ACK")
    
    # Ver número do ACK
    process(s, message)


def start(address: str, port: int, agent_name : str): 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    
    register(s, address, port, agent_name)
    
    while True:  
        message = s.recvfrom(1024) 
        print("recebi uma mensagem UDP!")
        threading.Thread(target=process, args=(s, message)).start() # uma thread por task

    s.close() 
    