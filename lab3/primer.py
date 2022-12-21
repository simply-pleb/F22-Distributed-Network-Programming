import math
from operator import truediv
import sys
from xmlrpc.client import Boolean
import zmq

SUB_TIMEOUT = 1000

worker_input_port = sys.argv[1]
worker_output_port = sys.argv[2]

context = zmq.Context()

def is_prime(n) -> Boolean:
    
    for i in range(2, int(math.sqrt(n)+1)):
        if n % i == 0:
            return False
    
    return True

# 1) connects to ZeroMQ sockets: worker_inputs, worker_outputs

client_input_socket = context.socket(zmq.SUB)
client_input_socket.connect(f"tcp://127.0.0.1:{worker_input_port}")
client_input_socket.setsockopt_string(zmq.SUBSCRIBE, 'isprime ')
# client_input_socket.RCVTIMEO = SUB_TIMEOUT

client_output_socket = context.socket(zmq.PUB)
client_output_socket.connect(f"tcp://127.0.0.1:{worker_output_port}")
while True:
    try:
        # 2) Receive message from the worker_inputs
        query = client_input_socket.recv_string()
        # if len(query) == 0:
        #     continue

        if len(query.split()) != 2:
            print("bad query")
            continue
        
        # 3) If message has following format “isprime N” then test number N for primeness
        requested = query.split(" ")[1]

        if not requested.isnumeric():
            continue
        
        num = int(requested)

        # 4) Send result to worker_outputs: “N is prime” or “N is not prime”
        message = f"{num} is prime" if is_prime(num) else f"{num} is not prime"
        client_output_socket.send_string(message)
    
    except zmq.Again:
        break
    except zmq.ZMQError:
        break