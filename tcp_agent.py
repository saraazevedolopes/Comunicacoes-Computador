import socket
import time

def send(s : socket.socket, agent_id : int, *args):
    fields : list = list()
    fields.append(bin(agent_id)[2:].zfill(5))     # id agente
    fields.append(bin(args[0])[2:].zfill(3))      # task type
    fields.append(bin(args[1])[2:].zfill(8))      # task ID
    
    
    print(f"ARGS: {args}")
    # CPU
    if args[0] in [0,1,2]:
        fields.append(bin(args[2])[2:].zfill(16))
    # Throughput 
    elif args[0] == 3:
        fields.append(bin(args[2])[2:].zfill(16)) # Throughput
        fields.append(format(ord(args[3]), '08b'))  # Unidade do throughput
        #fields.append(bin(args[4])[2:].zfill(16)) # Jitter
        #fields.append(bin(args[5])[2:].zfill(8))  # Losses 
    # Interfaces
    else:
        fields.append(bin(args[2])[2:].zfill(8)) # Estado da interface
            

    # Juntar todos os campos, pdu
    message : str = ''
    for field in fields:
        message += field

    # Conversão para bytes
    message_bytes = int(message, 2).to_bytes(len(message) // 8, byteorder='big')

    # Enviar mensagem pelo socket UDP
    s.send(message_bytes)

def start(address: str, port: int): 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # criar socket para receber syn
    #AF_INET diz que é ipv4
    #SOCK_STREAM diz que é TCP
    #s.bind(("10.0.0.2", port)) # não precisa de bind, porque não me importo que seja aleatório
    print(f"O tipo do s é {type(s)}")
    s.connect((address, port)) 

    send(s, 20, 1, 3, 80) # buffer de 1024 bytes para enviar mensagem (array de bytes)
    send(s, 30, 3, 4, 7, "M")

    time.sleep(30)
    