import threading
import sys
import udp_server
import tcp_server

def main(): 
    address, port = sys.argv[1], sys.argv[2]  
    print(f"Servidor iniciado em {address}:{port}")
    
    # Colocar outras mensagens de inicialização aqui, se necessário
    
    threads = [
        threading.Thread(target=udp_server.start, args=(address, int(port))), 
        threading.Thread(target=tcp_server.start, args=(address, int(port)))
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
