import sys
import zmq

writer_port = sys.argv[1]
my_name = sys.argv[2]

context = zmq.Context()

client_input_socket = context.socket(zmq.PUB)
client_input_socket.connect(f"tcp://127.0.0.1:{writer_port}")

while True:
    try:
        inp = input()
        message  = my_name + ": " + inp

        client_input_socket.send_string(message)
    
    except KeyboardInterrupt:
        break
    except:
        break