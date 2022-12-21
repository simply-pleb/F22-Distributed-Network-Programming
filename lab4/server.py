# python3 -m grpc_tools.protoc SimpleService.proto --proto_path=. --python_out=. --grpc_python_out=.
from audioop import reverse
from copyreg import pickle
import math
from wsgiref.handlers import SimpleHandler
import SimpleService_pb2 as pb2
import SimpleService_pb2_grpc as pb2_grpc
import grpc
from concurrent import futures
import sys

PORT = sys.argv[1]


def isPrime(num:int):
    for i in range(2, int(math.sqrt(num) + 1)):
        if num % i == 0:
            return False
    
    return True

class SimpleHandler(pb2_grpc.SimpleServiceServicer):
    def GetServerResponse(self, request, context):
        
        msg = request.message
        reply = {"message": msg, "received": True}
        
        return pb2.MessageResponse(**reply)

    def ReverseString(self, request, context):
        
        msg = request.message
        
        rpl = f"message: \"{msg[::-1]}\""
        reply = {"message": rpl, "received": True}
        
        return pb2.MessageResponse(**reply)
        
    def SplitString(self, request, context):
        
        msg = request.message        
        temp = msg.split(" ")
        
        data = [f"number: {len(temp)}"]
        for word in temp:
            print (word)
            data.append(f"parts: \"{word}\"")
        print(data)
        
        rpl = str(data)
        print(rpl)
        
        reply = {"message": rpl, "received": True}
        
        return pb2.MessageResponse(**reply)
    
    def IsPrime(self, request, context):
        
        msg = request.message
        temp = msg.split(" ")
        
        data = []
        for word in temp:
            
            if word.isnumeric():
                res = isPrime(int(word))
                if res:
                    data.append(f"{word} is prime")
                else:
                    data.append(f"{word} is not prime")
            else:
                data.append(f"{word} is not numeric")
            
        print(data)
        
        rpl = str(data)
        print(rpl)
        
        reply = {"message": rpl, "received": True}
        
        return pb2.MessageResponse(**reply)

# if __name__ == "main":
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
pb2_grpc.add_SimpleServiceServicer_to_server(SimpleHandler(), server)
server.add_insecure_port(f"127.0.0.1:{PORT}")
server.start()
try:
    server.wait_for_termination()
except:
    print("Shutting down")

