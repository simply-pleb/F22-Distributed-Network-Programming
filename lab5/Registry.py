import sys
import chord_pb2 as pb2
import chord_pb2_grpc as pb2_grpc
import grpc
from concurrent import futures
import random
import json

class RegistryHandler(pb2_grpc.RegistryServicer):
    
    def __init__(self, m):
        self.m = m
        self.id_port_dict = {}
        self.max_size = 2 ** m
    
    def register(self, request, context):
        """Missing associated documentation comment in .proto file."""
        try:
            request = request.message
            ipaddr, port = request.split(":")
            port = int(port)
            
            random.seed(0)
            if len(self.id_port_dict) == self.max_size:
                msg = "error. the Chord is full"    
                reply = {"received": False, "message": msg}
                return pb2.MessageResponse(**reply)
            
            while True:
                new_id = random.randrange(self.max_size)
                if new_id not in self.id_port_dict:
                    self.id_port_dict[new_id] = request
                    msg = json.dumps({"id": new_id, "m": self.m})    
                    reply = {"received": True, "message": msg}
                    
                    print(f"assigned node_id={new_id} to address {ipaddr}:{port}")
                    return pb2.MessageResponse(**reply)
        
        except:
            return {"received": False, "message": "register() error"}
        

    def deregister(self, request, context):
        """Missing associated documentation comment in .proto file."""
        
        try:
            request = request.message
            id = int(request)
            print("deregisteing", id)
            port = self.id_port_dict.pop(id)
            
            msg = f'Node {id} with port {port} was deregistered'
            reply = {"received": True, "message": msg}
            
            return pb2.MessageResponse(**reply)
        except:
            return {"received": False, "message": "deregister() error"}
        
    def populate_finger_table(self, request, context):
        """Missing associated documentation comment in .proto file."""

        try:
            request = request.message
            id = int(request)
            finger_table = {}
            for i in range(self.m ):
                passed = (id + 2 ** i) % self.max_size
                n_id = self._succ(passed)
                # print("fp alright", n_id)
                finger_table[str(n_id)] = self.id_port_dict[n_id]
            pred_node_id = self._pred(id)
            
            msg = json.dumps({ \
                    "pred_id": pred_node_id, \
                    "pred_addr": self.id_port_dict[pred_node_id], \
                    "finger_table": finger_table \
                })
            
            reply = {"received": True, "message": msg}
            return pb2.MessageResponse(**reply)
        except:
            return {"received": False, "message": "populate_finger_table() error"}
    
    def _succ(self, node_id):
        nodes = sorted(self.id_port_dict.keys())
        for next_node_id in nodes:
            if node_id <= next_node_id:
                return next_node_id
        return nodes[0]

    def _pred(self, node_id):
        nodes = sorted(self.id_port_dict.keys())
        nodes.reverse()
        for prev_node_id in nodes:
            if node_id > prev_node_id:
                return prev_node_id
        return nodes[0]

    def get_chord_info(self, request, context):
        """Missing associated documentation comment in .proto file."""
        
        # print(self.id_port_dict)
        msg = json.dumps(self.id_port_dict)
        reply = {"received": True, "message": msg}

        return pb2.MessageResponse(**reply)


def main():
    try:
        IP_PORT = sys.argv[1]
        M = int(sys.argv[2])
        # IP, PORT = IP_PORT.split(":")
        # PORT = int(PORT)
    except:
        return
        
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_RegistryServicer_to_server(RegistryHandler(M), server)
    server.add_insecure_port(f"{IP_PORT}")
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Keyboard interrupt. Shutting down")
    except:
        print("Undefined error. Shutting down")
    

if __name__ == "__main__":
    main()