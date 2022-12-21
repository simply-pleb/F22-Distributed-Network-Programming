import sys
import zmq

SUB_TIMEOUT = 200

client_input_port = sys.argv[1]
client_output_port = sys.argv[2]

context = zmq.Context()

def main_loop(client_input_socket:context.socket(zmq.REQ), client_output_socket:context.socket(zmq.SUB)):
    try:
        while True:    
            # 2) Read a line from the terminal
            line = input("> ")
            # 3) Send line to ZeroMQ
            try:
                if len(line) != 0:
                    client_input_socket.send_string(line)
                    try:
                        ack = client_input_socket.recv_string()
                        if ack != "ack":
                            print("bad ack. terminating client")
                            sys.exit(0)
                    except zmq.Again:
                        print("no ack. timed out")
                        break
            except:
                print("error sending message")
                break
            # 4) Receive a message from client_outputs and print it
            while True:
                try:
                    output = client_output_socket.recv_string()
                    print(output)
                except zmq.Again:
                    # print("receiving timed out")
                    break
    except KeyboardInterrupt:
        print("Terminating client")
        sys.exit(0)

# 1) Connect to server ZeroMQ sockets: client_inputs, client_outputs

client_input_socket = context.socket(zmq.REQ)
client_input_socket.connect(f"tcp://127.0.0.1:{client_input_port}")

client_output_socket = context.socket(zmq.SUB)
client_output_socket.connect(f"tcp://127.0.0.1:{client_output_port}")
client_output_socket.setsockopt_string(zmq.SUBSCRIBE, '')
client_output_socket.RCVTIMEO = SUB_TIMEOUT


# 2, 3, 4
main_loop(client_input_socket, client_output_socket)
