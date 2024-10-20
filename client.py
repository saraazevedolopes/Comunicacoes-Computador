import socket

def main(): 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 

    s.bind(("10.0.0.2", 2222)) 
    #sendto, 2 argumentos. 1º array de bytes a enviar, 2º para onde enviar
    s.sendto("olá <3".encode(), ("10.0.0.1", 1111)) # endecode: pega na string e converte para um array de bytes

if __name__ == "__main__":
    main()