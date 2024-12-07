import threading
import sys
import udp_server
import tcp_server
from app import web_app
import signal
import socket
import logger

def get_details():
    port = 999
    address = socket.gethostbyname("server")
    
    return address, port

def main():  
    log_level = sys.argv[1]
    address, port = get_details()

    agent_list : dict = dict()
    agent_data : dict = dict()
    agent_logs : dict = dict()

    agent_logs[0] = logger.server_console(log_level)
    
    def signal_handler(signal, frame):
        threads = list()
        try: 
            for agent in agent_list.keys():
                t = threading.Thread(target=udp_server.schedule_end(agent_list[agent].address[0], agent_list[agent].address[1], agent))
                threads.append(t)   
        except:
            pass

        for t in threads:
            t.daemon = True
            t.start()

        for t in threads:
            t.join()
        
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    
    threads = [
        threading.Thread(target=udp_server.start, args=(address, port, agent_list, agent_data, agent_logs, int(log_level))), 
        threading.Thread(target=tcp_server.start, args=(address, port, agent_data, agent_logs)),
    ]

    for t in threads:
        t.daemon = True
        t.start()

    web_app(address, agent_data)

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
