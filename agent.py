import threading
import sys
import udp_agent
import tcp_agent
from pythonping import ping 

def main(): 

    address, port, agent_name = sys.argv[1], sys.argv[2], sys.argv[3] # sys a ser usado para buscar input à linha de comandos
    print(f"{address} {port}")

    threads = [threading.Thread(target=udp_agent.start, args=(address, int(port), agent_name)), 
                threading.Thread(target=tcp_agent.start, args=(address, int(port)))]

    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()