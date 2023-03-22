import math
import sys
import zmq

SUB_TIMEOUT = 1000

worker_input_port = sys.argv[1]
worker_output_port = sys.argv[2]

context = zmq.Context()

# 1) connects to ZeroMQ sockets: worker_inputs, worker_outputs

client_input_socket = context.socket(zmq.SUB)
client_input_socket.connect(f"tcp://127.0.0.1:{worker_input_port}")
client_input_socket.setsockopt_string(zmq.SUBSCRIBE, 'gcd ')
# client_input_socket.RCVTIMEO = SUB_TIMEOUT

client_output_socket = context.socket(zmq.PUB)
client_output_socket.connect(f"tcp://127.0.0.1:{worker_output_port}")

while True:
    try:
        # 2) Receive message from the worker_inputs
        query = client_input_socket.recv_string()
        # if len(query) == 0:
        #     continue

        if len(query.split(" ")) != 3:
            print("bad query")
            continue
        
        # 3) If message has following format “gcd A B” then computes Greatest Common 
        #    Divisor for given two integers
        A = query.split(" ")[1]
        B = query.split(" ")[2]
        
        if not A.isnumeric() or not B.isnumeric():
            continue
        
        a = int(A)
        b = int(B)

        # 4) Send result to worker_outputs: “gcd for A B is C”
        message = f"gcd for {A} and {B} is {math.gcd(a, b)}"
        client_output_socket.send_string(message)
    
    except zmq.Again:
        break
    except zmq.ZMQError:
        break

