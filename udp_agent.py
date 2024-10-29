import socket
import parser
import threading

#Recebe uma mensagem UDP, desserializa o conteúdo de message[0] de bytes para um formato de dados utilizável 
#(como uma lista ou dicionário) usando parser.parse, e imprime o resultado.
def process(s : socket.socket, message : bytes):
    data = parser.parse(message[0])

    print(data)


def start(address: str, port: int, agent_name : str): 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 

    #s.bind((address, port)) não precisamos de ter porta e endereço fixo
    #sendto, 2 argumentos. 1º array de bytes a enviar, 2º para onde enviar
    s.sendto(agent_name.encode(), (address, port)) # endecode: pega na string e converte para um array de bytes

    message = s.recvfrom(1024)

    threading.Thread(target=process, args=(s, message)).start()