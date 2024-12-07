import socket
import parser
import threading
import logger

def process(message : bytes, agent_data : dict, agent_logs : dict):
    fields = parser.parse_tcp(message)
    #Agent ID, Task ID, Task_type, metric
    if fields[2] == 0:
        agent_logs[fields[0]].warning(f"ALERT received for task {fields[1]} from Agent{fields[0]}, METRIC={fields[3]}%")
    elif fields[2] == 1:
        agent_logs[fields[0]].warning(f"ALERT received for task {fields[1]} from Agent{fields[0]}, TASK_TYPE={fields[2]}, METRIC={fields[3]}%")
    elif fields[2] == 2:
        agent_logs[fields[0]].warning(f"ALERT received for task {fields[1]} from Agent{fields[0]}, TASK_TYPE={fields[2]}, METRIC={fields[3]}ms")
    elif fields[2] == 3:
        agent_logs[fields[0]].warning(f"ALERT received for task {fields[1]} from Agent{fields[0]}, TASK_TYPE={fields[2]}, METRIC={fields[3]}")
    else:
        agent_logs[fields[0]].warning(f"ALERT received for task {fields[1]} from Agent{fields[0]}, TASK_TYPE={fields[2]}, METRIC={fields[3]}")
    
    agent_data[str(fields[0])].add_alert(fields[1],fields[2],fields[3])

    
def agent_connection(connection: socket.socket, agents_data : dict, agent_logs : dict):
    while True:
        message = connection.recv(8) # buffer de 1024 bytes para receber mensagem (array de bytes)

        if len(message) == 0: # evitar spam de fim de conexão
            return
        threading.Thread(target=process, args=(message,agents_data, agent_logs)).start()

def start(address: str, port: int, agent_data : dict, agent_logs : dict): 
    #s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # criar socket para receber syn
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    #AF_INET diz que é ipv4
    #SOCK_STREAM diz que é TCP
    s.bind((address, port)) # associamos o socket a um par endereço-porta, podia ser a mesma porta

    s.listen(5) # ficar à escuta de pedidos de ligação (SYN), 5 - número de falhas até rejeitar a ligação, proteger de DDOS
    
    while True: 
        connection, agent_address = s.accept() # quando aceito uma ligação de um endereço, agent_address, recebo um socket (socket dentro de um socket para comunicação) 
        threading.Thread(target=agent_connection, args=(connection,agent_data, agent_logs)).start()
        
        
    

