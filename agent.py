import threading
import sys
import udp_agent
import tcp_agent
import socket
from queue import Queue
import signal
import netifaces
import logging
import logger

def signal_handler(signal, frame):
    s, address, port, agent_name, logger = get_details(0)
    udp_agent.schedule_end(address, int(port), agent_name)
    
    print(f"\nA FECHAR CORRETAMENTE DEPOIS DO END")
    sys.exit(0)

def get_details(log_level : int):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    ip = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
    port = 999
    server_ip = socket.gethostbyname("server")

    try:
        host_name = socket.getnameinfo((ip, 0),0)[0]
    except socket.gaierror:
        print(f"FATAL - Could not properly resolve DNS name")

    log_levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL, logging.FATAL]
    agent_name = host_name.split(".")[0][5:]
    agent_logger = logger.setup_logger('app', 'logs/agent'+agent_name+'/agent.log', False, level=log_level)
    
    return s, server_ip, port, agent_name, agent_logger

def main(): 
    log_level = int(sys.argv[1])
    s, address, port, agent_name, agent_logger = get_details(log_level)

    alert_queue = Queue()

    threads = [threading.Thread(target=udp_agent.start, args=(s, address, int(port), agent_name, alert_queue, agent_logger)), 
                threading.Thread(target=tcp_agent.start, args=(address, int(port), alert_queue))]

    for t in threads:   
        t.daemon = True
        t.start()

    for t in threads:
        t.join()



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()

    