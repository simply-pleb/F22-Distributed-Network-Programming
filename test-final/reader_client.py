import sys
import zmq

SUB_TIMEOUT = 10000

reader_port = sys.argv[1]
my_name = sys.argv[2]

context = zmq.Context()

client_output_socket = context.socket(zmq.SUB)
client_output_socket.connect(f"tcp://127.0.0.1:{reader_port}")
client_output_socket.setsockopt_string(zmq.SUBSCRIBE, '')
client_output_socket.RCVTIMEO = SUB_TIMEOUT

while True:
    try:
        reply = client_output_socket.recv_string()
        print(reply)
    except KeyboardInterrupt:
        break
    except:
        break