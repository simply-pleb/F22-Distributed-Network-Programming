import sys
import time
import zmq
from threading import Thread
from collections import OrderedDict

TIMER_INTERVAL = 5
SUB_TIMEOUT = 100

client_input_port = sys.argv[1]
client_output_port = sys.argv[2]

context = zmq.Context()

## bind writer_client
client_input_socket = context.socket(zmq.SUB)
client_input_socket.bind(f"tcp://127.0.0.1:{client_input_port}")
client_input_socket.setsockopt_string(zmq.SUBSCRIBE, '')
client_input_socket.RCVTIMEO = SUB_TIMEOUT

## bind reader_client
client_output_socket = context.socket(zmq.PUB)
client_output_socket.bind(f"tcp://127.0.0.1:{client_output_port}")

# ---

is_time_to_send = False 
storage = OrderedDict()

def form_summary_message():
    message = ""
    try:
        for key, vals in storage.items():
            print(key)            
            for elem in vals:
                message += elem + "\n"
    except:
        storage = OrderedDict()
        return message + "SUMMARY:\n"
        
    message += "SUMMARY:\n"
        
    try:
        for key in sorted(storage.keys()):
            message += "  " + key + " " + len(storage.get(key)) + "\n"
    except:
        storage = OrderedDict()
        return message
    
    storage = OrderedDict()
    
    return message

def work_timer_interval():
    while True:
        time.sleep(TIMER_INTERVAL)
        is_time_to_send = True

# def send_to_reader():
#     is_time_to_send = False    

worker = Thread(target=work_timer_interval)
worker.start()

while True:
    # 2) Receive message from the writer_client, send the message to reader_client
    try:
        time_to_send = time.time() + TIMER_INTERVAL
        while time.time() < time_to_send:
            try:
                client_message = client_input_socket.recv_string()
                name, mesg = client_message.split(": ")
                print(name, ":", mesg)
                if storage.get(name) == None:
                    storage[name] = []
                
                storage.get(name).append(mesg)
            except zmq.ZMQError:
                # print("ZMQError")
                continue
            
        # if is_time_to_send == True:
        # print("!")
        print(storage)
        is_time_to_send = False
        message = form_summary_message()
        client_output_socket.send_string(message)
        print("Message sent to reader:")
        print(message)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        break
    except:
        print("some error")
    

