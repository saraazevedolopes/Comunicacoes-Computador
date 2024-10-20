import socket

def main(): 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # criar socket
    #AF_INET diz que é ipv4
    #SOCK_DGRAM diz que é UDP
    s.bind(("10.0.0.1", 1111)) # associei o socket a um par endereço-porta
    mensagem = s.recvfrom(1024) # buffer de 1024 bytes para receber mensagem (array de bytes)
    print(mensagem[0].decode())
    print(mensagem[1])

if __name__ == "__main__":
    main()