import threading
import sys
import udp_server
import tcp_server

def main(): 

    address, port = sys.argv[1], sys.argv[2] # sys a ser usado para buscar input à linha de comandos
    print(f"{address} {port}")
    threads = [threading.Thread(target=udp_server.start, args=(address, int(port))), # a função udp_server vai correr na thread t1 com o argumento (address, port)
                threading.Thread(target=tcp_server.start, args=(address, int(port)))]

    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()