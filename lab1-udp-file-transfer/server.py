import socket
import time
import sys

UDP_IP = 'localhost'#"<ip_address_of_receiver>"
UDP_PORT = int(sys.argv[1])

ENCOD = "UTF-8"
WAIT_TIME = 3
BUFFSIZE = 1024

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

sock.settimeout(WAIT_TIME)

print("server started")

def parse_start_from_client(message):

    prefix, rest = message.split(" | ".encode(ENCOD), 1)
    seqno, rest = rest.split(" | ".encode(ENCOD), 1)
    filename, file_size = rest.split(" | ".encode(ENCOD), 1)
    
    prefix = prefix.decode(ENCOD)
    seqno = int(seqno.decode(ENCOD))
    filename = filename.decode(ENCOD)
    file_size = int(file_size.decode(ENCOD))

    return prefix, seqno, filename, file_size

def parse_data_from_client(message):
    
    prefix, rest = message.split(" | ".encode(ENCOD), 1)
    seqno, data_bytes = rest.split(" | ".encode(ENCOD), 1)
    
    prefix = prefix.decode(ENCOD)
    seqno = int(seqno)
    data_bytes = bytes(data_bytes)

    return prefix, seqno, data_bytes

def start_data_receiving(message, address):
    
    prefix, seqno, filename, file_size = parse_start_from_client(message)
    started = False

    if prefix == "s":
        started = True
        # client_addr = address
        message = f"a | {seqno + 1} | {BUFFSIZE}"
        sock.sendto(message.encode(ENCOD), address)
    
    if(started):
        print(f"established a connection with {address}")
        receive_data(filename, file_size)
    
    else:
        print(f"did not start connection with client:{address}")

def receive_data(filename, file_size):
    bytes_to_save = b""
    succeeded = True
    while len(bytes_to_save) < file_size:
        try:
            message, address = sock.recvfrom(BUFFSIZE)
            
            prefix, seqno, data_bytes = parse_data_from_client(message)

            if prefix == "d":
                print (f"received chunk {seqno}")
                message = f"a | {seqno + 1}"
                sock.sendto(message.encode(ENCOD), address)
                bytes_to_save += data_bytes    
        
        except:
            print("failed to receive data chunk")
            succeeded = False
            break

    if succeeded:
        filee = open(filename, "wb+").write(bytes_to_save)
        print(f"{filename} was successfully received")
        print("¿holding information for 1s?")
        time.sleep(1)

    else:
        print(f"{filename} has failed to be received")  

while True:
    try:
        print("waiting for a connection...")
        message, address = sock.recvfrom(BUFFSIZE)
        start_data_receiving(message, address)

    except:
        print(f"No connections for the last {WAIT_TIME}s. terminating server...")
        break

print("server was terminated.")