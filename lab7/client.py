import grpc

import raft_pb2
import raft_pb2_grpc

# dict_id_addr = {}

class Client():
    def __init__(self):
        self.stub = None
    def connect(self, ip_port:str):
        try:
            channel = grpc.insecure_channel(ip_port)
            self.stub = raft_pb2_grpc.ServerStub(channel)
        except:
            print("something went wrong in connection")
    def getleader(self):
        
        try:
            msg = raft_pb2.EmptyMessage()
            reply = self.stub.GetLeader(msg)
            print(reply.message)
        except:
            print("something went wrong in getting leader")
        
    def suspend(self, time):
        try:
            msg = raft_pb2.Message(message=f"{time}")
            reply = self.stub.Suspend(msg)
        except:
            print("something went wrong in suspending")
        # print(reply)
    def setval(self, key, value):
        try:
            msg = raft_pb2.MessageKeyValue(key=f"{key}", value=f"{value}")
            reply = self.stub.SetVal(msg)
        except:
            print("something went wrong in setting the value")
    def getval(self, key):
        try:
            msg = raft_pb2.MessageKey(key=f"{key}")
            reply = self.stub.GetVal(msg)
            print(reply.message)
        except:
            print("something went wrong in getting the value")

    def quit(self):
        print("The client ends")

if __name__ == "__main__":
    # file = open("Config.conf", "r")
    # lines = file.readlines()
    
    # for line in lines:
    #     line = line.split(" ")
    #     id = line[0]
    #     addr = (line[1] + ":" + line[2]).replace('\n', '')
    #     dict_id_addr[id] = addr
    
    client = Client()
    while True:
        try:
            line = input("> ").split()
            if line[0] == 'connect':
                SERVER_ADDRESS = line[1] + ":" + line[2]
                client.connect(SERVER_ADDRESS)
            elif line[0] == 'getleader':
                client.getleader()
            elif line[0] == 'suspend':
                client.suspend(line[1])
            elif line[0] == 'setval':
                client.setval(line[1], line[2])
            elif line[0] == 'getval':
                client.getval(line[1])
            elif line[0] == 'quit':
                client.quit()
                break
            else:
                print("Undefined command")
        except KeyboardInterrupt:
            print("Keyboard interrupt")
            client.quit()
            break