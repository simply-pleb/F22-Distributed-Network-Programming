import sys
import time
import zmq

SUB_TIMEOUT = 1000

client_input_port = sys.argv[1]
client_output_port = sys.argv[2]
worker_input_port = sys.argv[3]
worker_output_port = sys.argv[4]

context = zmq.Context()

# 1) Binds ZeroMQ sockets: client_inputs, client_outputs, worker_inputs, worker_outputs

## 1.1) bind client_input
client_input_socket = context.socket(zmq.REP)
client_input_socket.bind(f"tcp://127.0.0.1:{client_input_port}")

## 1.2) bind client_output
client_output_socket = context.socket(zmq.PUB)
client_output_socket.bind(f"tcp://127.0.0.1:{client_output_port}")

## 1.3) bind worker_input
worker_input_socket = context.socket(zmq.PUB)
worker_input_socket.bind(f"tcp://127.0.0.1:{worker_input_port}")

## 1.4) bind worker_output
worker_output_socket = context.socket(zmq.SUB)
worker_output_socket.bind(f"tcp://127.0.0.1:{worker_output_port}")
worker_output_socket.setsockopt_string(zmq.SUBSCRIBE, '')
worker_output_socket.RCVTIMEO = SUB_TIMEOUT


while True:
        # 2) Receive message from the client_inputs, send the message to worker_inputs
        try:
            client_message = client_input_socket.recv_string()
        except zmq.ZMQError:
            continue

        ## transmit message
        client_input_socket.send_string("ack")
        worker_input_socket.send_string(client_message)
        client_output_socket.send_string(client_message)

        # 3) Receive message from worker_outputs, send message to client_outputs
        while True:
            try:
                worker_message = worker_output_socket.recv_string()
                client_output_socket.send_string(worker_message)
            except zmq.Again:
                break
            except zmq.ZMQError:
                break

