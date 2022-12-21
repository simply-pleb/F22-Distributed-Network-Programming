import socket
import sys

def main():
    try:
        IP_PORT = sys.argv[1]
        NAME = sys.argv[2]
    except:
        print("invalid input")
        return
    
    # print(IP_PORT)
    
    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_STREAM) # TCP
    
    ip, port = IP_PORT.split(":")[0], \
                int(IP_PORT.split(":")[1])
    
    sock.connect((ip, port))

    # Send
    sock.sendall(NAME)

    # Receive
    while True:
        data = sock.recv(1024)
        print(data)
    

if __name__ == "__main__":
    main()