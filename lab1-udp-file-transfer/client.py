from fileinput import filename
import socket
import sys
from time import sleep

UDP_IP, UDP_PORT = sys.argv[1].split(":", 1)
UDP_PORT = int(UDP_PORT)
FILEPATH = sys.argv[2]
FILENAME = sys.argv[3]

ENCOD = "UTF-8"
WAIT_TIME = 0.5
BUFFSIZE = 1024


# establish udp connection
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

print(f"client started")

sock.settimeout(WAIT_TIME)

def parse_start_ack(message):
    prefix, rest = message.split(" | ".encode(ENCOD), 1)

    # # prefix gonna be b"d"
    seqno, bufsize = rest.split(" | ".encode(ENCOD), 1)
    
    prefix = prefix.decode(ENCOD)
    seqno = int(seqno.decode(ENCOD))
    bufsize = int(bufsize.decode(ENCOD))

    return prefix, seqno, bufsize

def parse_data_ack(message):
    prefix, seqno = message.split(" | ".encode(ENCOD), 1)
    
    prefix = prefix.decode(ENCOD)
    seqno = int(seqno.decode(ENCOD))

    return prefix, seqno

def send_data(buffsize):
    
    seqno_0 = 0
    
    # send data to server
    # "d | seqno_0+1 | data-bytes"
    cur_data_idx = 0
    ack_cnt = 0
    while cur_data_idx < file_size and ack_cnt < 5:
        # send a chunk
        
        data_message = f"d | {seqno_0} | "
        next_data_idx = min(cur_data_idx + buffsize - len(data_message), file_size)
        data_message = data_message.encode(ENCOD)
        data_message += filee[cur_data_idx : next_data_idx]
        
        try:
            sock.sendto(data_message, (UDP_IP, UDP_PORT))

            message, address = sock.recvfrom(BUFFSIZE)

            prefix, seqno = parse_data_ack(message)
            
            if prefix == "a":
                print(f"chunk {seqno_0} sent")
                cur_data_idx = next_data_idx
                seqno_0 = seqno
                ack_cnt = 0
        
        except:
            print(f"data ack was not received {ack_cnt} times in a row. resending data chunk {seqno_0}...")
            sock.sendto(data_message, (UDP_IP, UDP_PORT))
            ack_cnt += 1
    
    return ack_cnt < 5        

def start_connection(seqno_0, file_size):
    # send start message from client to server
    # "s | seqno_0 | filename | size "

    start_msg = f"s | {seqno_0} | {FILENAME} | {file_size}"

    sock.sendto(start_msg.encode(ENCOD), (UDP_IP, UDP_PORT))
    server_bufsize = 0
    # wait for acknowledgement for start
    ack_cnt = 0
    while ack_cnt < 5:
        try:
            message, address = sock.recvfrom(BUFFSIZE)

            # print(message)

            prefix, seqno, bufsize = parse_start_ack(message)
            
            if prefix == "a":
                seqno_0 = seqno
                server_bufsize = bufsize
                ack_cnt = 0
                break
    
        except:
            print(f"start ack was not received {ack_cnt} times in a row. resending start...")
            sock.sendto(start_msg.encode(ENCOD), (UDP_IP, UDP_PORT))
            ack_cnt += 1
    
    return server_bufsize

# ---

filee = open(FILEPATH, "rb").read()
file_size = len(filee)


server_bufsize = start_connection(0, file_size)

if server_bufsize > 0:
    print("connection has started")
    data_sent = send_data(server_bufsize)
    if data_sent:
        print(f"{FILEPATH} was sent successfully as {FILENAME}")
    else:
        print(f"{FILEPATH} was not sent")

else:
    print("Connection has timed out")