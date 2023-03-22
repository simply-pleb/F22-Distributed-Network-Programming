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

def must_be_equal(actual:int, supposed:int):
        if actual > supposed:
            raise ValueError("Too many arguments for the command")
        if actual < supposed:
            raise ValueError("Too few arguments for the command") 

class NodeHandler(pb2_grpc.NodeServicer):
    
    def __init__(self, ip_port, registry_stub:pb2_grpc.RegistryStub):
        self.ip_port = ip_port
        self.registry_stub = registry_stub
        self.finger_table = {}
        self.local_files = []
        self.pred_node = ()
        self.pred_ip_port = ""
        self.node_id = -1
        self.m = -1
        
        self._register()
        
        self.run_event = threading.Event()
        self.run_event.set()
        self.worker = threading.Thread(target=self._cont_populate_ft, args=(1,self.run_event))
        self.worker.start()
        # self.network_size = -1        
    
    def _register(self):
        try:
            msg = pb2.Message(message=str(self.ip_port))
            # print(msg)
            rpl = self.registry_stub.register(msg)
            # rpl = ast.literal_eval(rpl.message)
            # print (rpl)
            if rpl.received == True:
                rcvd = json.loads(rpl.message)
                self.m = rcvd["m"]
                self.node_id = rcvd["id"]
                print("registered node ", self.node_id)
                return True
            else:
                print("Failed to register this node")
        except:
            print("some problem with registering a node")
        
        return False
    
    def _cont_populate_ft(self, _, run_event:threading.Event):
        try:
            # print("?")
            while(run_event.is_set()):
                # print("populating")
                prev_pred = self.pred_node
                self._populate_ft()
                if prev_pred != self.pred_node and self.pred_node != self.node_id:
                    print(f"{self.node_id} predecessor is {self.pred_node}")
                    self._relocate_files(prev_pred)
                sleep(1)
        except KeyboardInterrupt:
            pass
    
    def _relocate_files(self, prev_pred):
        
        files = self.local_files.copy()
        
        # print(str(self.pred_node), self.pred_ip_port)
        dest_addr = self.pred_ip_port
        channel = grpc.insecure_channel(dest_addr)
        to_node_stub = pb2_grpc.NodeStub(channel)
        
        for file in files:
            hash_value = zlib.adler32(file.encode())
            target_id = (hash_value % 2**self.m + 1)
            
            if self._is_between(int(prev_pred)+1, int(self.pred_node), 2**self.m, target_id):
                self.local_files.remove(file)
                msg = pb2.Message(message=f"{file} ")
                to_node_stub.save(msg)
                
        pass
        
    def _populate_ft(self):
        try:
            msg = pb2.Message(message=str(self.node_id))
            rpl = self.registry_stub.populate_finger_table(msg)
            if rpl.received == True:
                rcvd = json.loads(rpl.message)
                self.pred_node = rcvd["pred_id"]
                self.pred_ip_port = rcvd["pred_addr"]
                self.finger_table = rcvd["finger_table"]
                
                # TODO: remove print
                # print(f"registered node {self.node_id} with finger table:")
                # print(self.finger_table)
                
                return True
            else:
                print("Failed to populate the finger table")
        except:
            print("some error with populating the finger table  ")
            pass
        return False
    
    def _deregister(self):
        try:
            print("dereg")
            msg = pb2.Message(message=str(self.node_id))
            rpl = self.registry_stub.deregister(msg)
            if rpl.received == True:
                print(rpl.message)
                return True
            else:
                print("Failed to deregister this node")
        except:
            print("some problem with deregistering a node")
        
        return False
    
    def get_finger_table(self, request, context):
        """Missing associated documentation comment in .proto file."""
        reply = {"received": True, "message": json.dumps(self.finger_table)}
        return pb2.MessageResponse(**reply)

    def save(self, request, context):
        """Missing associated documentation comment in .proto file."""
        try:
            request = request.message
            temp = request.split(" ", 1)
            must_be_equal(len(temp), 2)
            key, text = temp
            
            return self._save(key, text)
        except:
            print("some problem with saving")
            pass
         

    def remove(self, request, context):
        """Missing associated documentation comment in .proto file."""
        
        try:
            request = request.message
            temp = request.split(" ")
            must_be_equal(len(temp), 1)
            
            key = temp[0] 
            
            return self._remove(key)
        except:
            print("some problem with removing")
            pass
                
        
    def find(self, request, context):
        """Missing associated documentation comment in .proto file."""
        try:
            request = request.message
            temp = request.split(" ")
            must_be_equal(len(temp), 1)
            
            key = temp[0] 
            
            return self._find(key)
        except:
            print("some problem with finding")
            pass

    def quit(self, request, context):
        """Missing associated documentation comment in .proto file."""
        try:
            must_be_equal(len(request.split()), 0)
            self.quit_local()
            
        except ValueError:
            print(ValueError)
        except:
            pass
        return False        
    
    def quit_local(self):
        try:
            print("quitting")
            # key = request
            success = self._deregister()
            if success:
                self._notify_succ()
                self._transfer_data()
                self._notify_pred()
                # TODO: terminate
                return True 
            
        except ValueError:
            print(ValueError)
        except:
            pass
        return False     
    
    def _notify_succ(self):
        pass
    def _notify_pred(self):
        pass
    def _transfer_data(self):
        # TODO: give data to successor
        dest_addr = self.finger_table[self._succ()]
        channel = grpc.insecure_channel(dest_addr)
        to_node_stub = pb2_grpc.NodeStub(channel)
        
        for file in self.local_files:
            msg = pb2.Message(message=f"{file} ")
            to_node_stub.save(msg)
        self.local_files.clear()
    
    # def _
    def _is_between(self, l:int, r:int, max:int, target:int) -> Bool: 
        print("saving locally")
        if (l == max + 1):
            l = 1
        if (r == 0):
            r = max
        if (l < r):
            return l <= target <= r
        else :
            return l <= target <= max or 1 <= target <= r

    # # some function that returns the predesesor of node with this numb
    # int pred(int node_numb); 
    def _pred(self):
        return self.pred_node
        pass

    # # some function that returns the successor of node with this numb
    # int succ(int node_numb); 
    def _succ(self):
        finger_table_keys = [int(keys) for keys in self.finger_table.keys()]
        nodes = sorted(finger_table_keys)
        for next_node_id in nodes:
            if self.node_id <= next_node_id:
                return str(next_node_id)
        return str(nodes[0])

    # # some function that returns finger table
    # list FT(int node_numb);
    
    def _lookup(self, key):
        succ = self._succ()
        hash_value = zlib.adler32(key.encode())
        target_id = (hash_value % 2**self.m + 1)  
        
        # print("wath")
        # print(self._pred() + 1, self.node_id, 2**self.m, target_id)
        
        if self._is_between(int(self._pred()) + 1, int(self.node_id), int(2**self.m), int(target_id)):
            return str(self.node_id)

        elif self._is_between(int(self.node_id) + 1, int(self._succ()), int(2**self.m), int(target_id)):
            return str(succ)
            
        else:
            finger_table_keys = [int(keys) for keys in self.finger_table.keys()]
            finger_table_keys = sorted(finger_table_keys)
            
            for i in range(len(finger_table_keys)-1):
                cur = finger_table_keys[i]
                next = finger_table_keys[i+1]
                if self._is_between(cur, next, 2**self.m, target_id):
                    return str(cur)
            # if did not save on upper ones
            # save in finger_table(finger_table.size() - 1)
            return str(finger_table_keys[-1])
        
    def _save(self, key:str, text:str):
        dest_id = self._lookup(key)
        if dest_id == str(self.node_id):
            #save in this node
            if key in self.local_files:
                msg = f"{key} already exists in node {self.node_id}"
                reply = {"received": False, "message": msg}

                return pb2.MessageResponse(**reply)
            self.local_files.append(key)
            msg = f"{key} is saved in node {self.node_id}"
            reply = {"received": True, "message": msg}
            return pb2.MessageResponse(**reply)
        
        else:
            dest_addr = self.finger_table[dest_id]
            channel = grpc.insecure_channel(dest_addr)
            to_node_stub = pb2_grpc.NodeStub(channel)
            
            msg = pb2.Message(message=f"{key} {text}")
            return to_node_stub.save(msg)
    
    def _remove(self, key):
        dest_id = self._lookup(key)
        if dest_id == str(self.node_id):
            #remove from this node
            if key not in self.local_files:
                msg = f"{key} does not exists in node {self.node_id}"
                reply = {"received": False, "message": msg}

                return pb2.MessageResponse(**reply)
            
            self.local_files.remove(key)
            msg = f"{key} is removed from node {self.node_id}"
            reply = {"received": True, "message": msg}

            return pb2.MessageResponse(**reply)
        
        else:
            dest_addr = self.finger_table[dest_id]
            channel = grpc.insecure_channel(dest_addr)
            to_node_stub = pb2_grpc.NodeStub(channel)
            
            msg = pb2.Message(message=f"{key}")
            return to_node_stub.remove(msg)
    
    def _find(self, key):
        dest_id = self._lookup(key)
        if dest_id == str(self.node_id):
            #find in this node
            if key not in self.local_files:
                msg = f"{key} does not exists in node {self.node_id}"
                reply = {"received": False, "message": msg}

                return pb2.MessageResponse(**reply)

            msg = f"{key} is saved in node {self.node_id}"
            reply = {"received": True, "message": msg}

            return pb2.MessageResponse(**reply)
        
        else:
            dest_addr = self.finger_table[dest_id]
            channel = grpc.insecure_channel(dest_addr)
            to_node_stub = pb2_grpc.NodeStub(channel)
            
            msg = pb2.Message(message=f"{key}")
            return to_node_stub.find(msg)    
        
    def get_node_id(self, request, context):
        reply = {"received": True, "message": str(self.node_id)}
        return pb2.MessageResponse(**reply)
        # return super().get_node_id(request, context)        

def main():
    try:
        IP_PORT_SRVR = sys.argv[1]
        IP_PORT_NODE = sys.argv[2]
        # IP, PORT = IP_PORT.split(":")
        # PORT = int(PORT)
    except:
        return
    
    channel = grpc.insecure_channel(IP_PORT_SRVR)
    registry_stub = pb2_grpc.RegistryStub(channel)
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node_handler = NodeHandler(IP_PORT_NODE, registry_stub)
    pb2_grpc.add_NodeServicer_to_server(node_handler, server)
    server.add_insecure_port(f"{IP_PORT_NODE}")
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Terminating node...")
        node_handler.run_event.clear()
        node_handler.worker.join()
        node_handler.quit_local()
        print("Keyboard interrupt. Shutting down")
        # sys.exit()
    except:
        print("Undefined error. Shutting down")
    

if __name__ == "__main__":
    main()