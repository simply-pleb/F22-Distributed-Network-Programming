from concurrent import futures
import sys
from bleach import Cleaner

import grpc
import queue_pb2_grpc as pb2_grpc
import queue_pb2 as pb2

from threading import Thread
from multiprocessing import Queue

class Client():
    
    def __init__(self):
        self.stub = None
        self.server_addr = ""
        pass
    
    def connect_to(self, ip_port:str):
        try:
            ip, port = ip_port.split(":")[0], \
                int(ip_port.split(":")[1])
            
            
            channel = grpc.insecure_channel(ip_port)
            self.stub =  pb2_grpc.ServerStub(channel)
            print(ip_port)
            self.server_addr = ip_port
            # channel = grpc.insecure_channel(ip_port)
            # if self.registry_addr == None or self.registry_addr == ip_port:
            #     # connect to registry
            #     self.registry_addr = ip_port
            #     self.stub =  pb2_grpc.RegistryStub(channel)
            
        except Exception as e:
            print(e.args)
        
    def put(self, arg):
        msg = pb2.Message(message=f"{arg}")
        reply = self.stub.put(msg)
        return reply
        print(f"{reply.received}, {reply.message}")
        
    def peek(self):
        msg = pb2.EmptyMessage()
        reply = self.stub.peek(msg)
        return reply
        print(f"{reply.received}, {reply.message}")
    
    def pop(self):
        msg = pb2.EmptyMessage()
        reply = self.stub.pop(msg)
        return reply
        print(f"{reply.received}, {reply.message}")
    
    def size(self):
        msg = pb2.EmptyMessage()
        reply = self.stub.size(msg)
        
        return reply 
        print(f"{reply.received}, {reply.message}")
    
    def handle_input(self, arg:str):
        argv = arg.split() 
        op = argv[0]
        
        argv.pop(0)
        argc = len(argv)
        
        if op == "put":
            return self.put(argv[0])

        elif op == "peek" and argc == 0:
            return self.peek()

        elif op == "pop" and argc == 0:
            return self.pop()

        elif op == "size" and argc == 0:
            return self.size()
        else:
            raise ValueError("Undefined command")
        
    def quit():
        pass
        
def main():
    
    try:
        IP_PORT = sys.argv[1]
    except:
        print("incorrect system arguments")
        return
    
    client = Client()
    client.connect_to(IP_PORT)
    
    while (True):
        try:
            arg = input("> ")
            reply = client.handle_input(arg)
            
            print(reply.message)
            
        except KeyboardInterrupt:
            # client.quit()
            break
        except ValueError:
            print (ValueError)
        except:
            print ("Undefined error")
 
    
if __name__ == "__main__":
    main()