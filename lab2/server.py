from cmath import sqrt
import math
import socket

from threading import Thread
from multiprocessing import Queue
import pickle

NUM_OF_THREADS = 7
TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024
WAIT_TIME = 3

# Server setup
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind((TCP_IP, TCP_PORT))
soc.listen(NUM_OF_THREADS*100)
soc.settimeout(WAIT_TIME)

# Our function
def is_prime(n):
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    for divisor in range(3, int(math.sqrt(n)+1), 2):
        if n % divisor == 0:
            return False
    return True

# Threads section
que_requests = Queue()
bThread_is_free = []
nThread_data = []

## A target function for the threads that will run the whole life-time of the thread and wait for data  
def work_is_prime(thrd_idx):
    while True:
        if que_requests.empty():
            break

        conn, addr = que_requests.get()
        if conn:
            print(f"Started - Thread {thrd_idx} working with {addr}")
            while True:
                data = conn.recv(BUFFER_SIZE)
                
                if not data:
                    # print("No more data")
                    break
                
                recvd_number = pickle.loads(data)

                # print("received data:", repr(recvd_number))
                
                message = f"{recvd_number} is {'prime' if is_prime(recvd_number) else 'not prime'}"
                # print(f"message to be sent: {message}")
                conn.send(message.encode())

            conn.close()
            print(f"Finished - Thread {thrd_idx} closes connection with {addr}")
        # conn.send(data)  # echo
    print(f"Thread {thrd_idx} terminated")



## Thread declaration
working_threads = [Thread(target=work_is_prime, args=(i, )) for i in range(NUM_OF_THREADS)]

## Handle receiving requests
while True:
    try:
        conn, addr = soc.accept()  
        print("[-] Connected to " + addr[0] + ":" + str(addr[1]))      
        que_requests.put([conn, addr])
    except:
        print("No more new clients")
        break

print(f"amount of clients: {que_requests.qsize()}")

[t.start() for t in working_threads]
[t.join() for t in working_threads]

