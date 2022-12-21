import ast
from email import message
import json
import sys
import threading
from time import sleep
import zlib

from traitlets import Bool
import chord_pb2 as pb2
import chord_pb2_grpc as pb2_grpc
import grpc
from concurrent import futures

class Client():
    
    def __init__(self):
        self.registry_addr = None
        self.is_connected_to_reg = False
        self.stub = None
        self.node_id = -1
        pass
    def connect(self, ip_port:str):
        
        try:
            ip, port = ip_port.split(":")[0], \
                int(ip_port.split(":")[1])
            
            channel = grpc.insecure_channel(ip_port)
            if self.registry_addr == None or self.registry_addr == ip_port:
                # connect to registry
                self.registry_addr = ip_port
                self.stub =  pb2_grpc.RegistryStub(channel)
                self.is_connected_to_reg = True
                self.node_id = -1
                print("Connected to Registry")
            else:
                # connect to node
                self.stub =  pb2_grpc.NodeStub(channel)
                self.is_connected_to_reg = False
                
                msg = pb2.EmptyMessage()
                self.node_id = self.stub.get_node_id(msg).message
                print("Connected to Node")
        
        except:
            print("Address is neither Node nor Registry")
        # TODO: connect to node or registry
         
    def get_info(self):
        if self.is_connected_to_reg == True:
            msg = pb2.EmptyMessage()
            reply = self.stub.get_chord_info(msg)
            
            info = json.loads(reply.message)
            # print(info)
            for key in info.keys():
                print(f"{key}:\t{info[key]}")
        else:
            msg = pb2.EmptyMessage()
            reply = self.stub.get_finger_table(msg)
            
            info = json.loads(reply.message)
            
            print("Node id:", self.node_id)
            print("Finger table:")
            for key in info.keys():
                print(f"{key}:\t{info[key]}")
            # print("You are not connected to a Registry")
    
    def save(self, key:str, text:str):
        if self.is_connected_to_reg == True:
            print ("You are not connected to a Node")
            return 
        
        key = key.replace('"', '')
        
        msg = pb2.Message(message=f"{key} {text}")
        print ("!!")
        reply = self.stub.save(msg)
        
        print(f"{reply.received}, {reply.message}")
        
    def remove(self, key):
        if self.is_connected_to_reg == True:
            print ("You are not connected to a Node")
            return 
        key = key.replace('"', '')
        
        msg = pb2.Message(message=f"{key}")
        reply = self.stub.remove(msg)
        
        print(f"{reply.received}, {reply.message}")

    def find(self, key):
        if self.is_connected_to_reg == True:
            print ("You are not connected to a Node")
            return
        key = key.replace('"', '')
        
        msg = pb2.Message(message=f"{key}")
        reply = self.stub.find(msg)
        
        print(f"{reply.received}, {reply.message}")
        

    def quit(self):
        print("Terminating")
        pass
    
    def must_be_equal(self, actual:int, supposed:int):
        if actual > supposed:
            raise ValueError("Too many arguments for the command")
        if actual < supposed:
            raise ValueError("Too few arguments for the command")
    
    def process(self, arg:str):
        argv = arg.split() 
        op = argv[0]
        
        
        argv.pop(0)
        argc = len(argv)
        
        if op == "connect":
            # print(argv, argc)
            self.must_be_equal(argc, 1)
            self.connect(argv[0])

        elif op == "get_info":
            self.must_be_equal(argc, 0)
            self.get_info()

        elif op == "save":
            self.must_be_equal(argc, 2)
            self.save(argv[0], argv[1])

        elif op == "remove":
            self.must_be_equal(argc, 1)
            self.remove(argv[0])

        elif op == "find":
            self.must_be_equal(argc, 1)
            self.find(argv[0])
            
        elif op == "quit":
            self.must_be_equal(argc, 0)
            self.remove()
            pass
        else:
            raise ValueError("Undefined command")
        
        pass

if __name__ == "__main__":
    client = Client()
    
    while (True):
        try:
            arg = input("> ")
            client.process(arg)
        except KeyboardInterrupt:
            client.quit()
            break
        except ValueError:
            print (ValueError)
        except:
            print ("Undefined error")
