from urllib import response
import grpc
import SimpleService_pb2 as pb2
import SimpleService_pb2_grpc as pb2_grpc

import ast

import sys

ADDR = sys.argv[1]


channel = grpc.insecure_channel(ADDR)
stub = pb2_grpc.SimpleServiceStub(channel)


while True:
    line = input("> ")
    
    if line.startswith("reverse"):
        msg = pb2.Message(message=line.split(" ", 1)[1])
        response = stub.ReverseString(msg)
        print(response.message)

    elif line.startswith("split"):
        msg = pb2.Message(message=line.split(" ", 1)[1])
        response = stub.SplitString(msg)
        
        rcvd = ast.literal_eval(response.message)
        
        for part in rcvd:
            print(part)
        
    elif line.startswith("isprime"):
        msg = pb2.Message(message=line.split(" ", 1)[1])
        response = stub.IsPrime(msg)
        
        rcvd = ast.literal_eval(response.message)
        
        for part in rcvd:
            print(part)
            
    elif line.startswith("exit"):
        print("terminating client...")
        break
    
    else:
        print ("no such command: " + line)
        
print("client terminated.")