# from copyreg import pickle
import socket
import sys
import pickle

TCP_IP, TCP_PORT = sys.argv[1].split(":", 1)
TCP_PORT = int(TCP_PORT)
BUFFER_SIZE = 1024
WAIT_TIME = 30
MESSAGE = "Hello, World!"

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(f"connecting to {TCP_IP}:{TCP_PORT}")
soc.connect((TCP_IP, TCP_PORT))
soc.settimeout(WAIT_TIME)

numbers = [ 15492781, 15492787, 15492803,
            15492811, 15492810, 15492833,
            15492859, 15502547, 15520301,
            15527509, 15522343, 1550784]

for num in numbers:    
    num_byte = pickle.dumps(num)
    soc.send(num_byte)
    data = soc.recv(BUFFER_SIZE)

    print("received data:", data.decode())


soc.close()