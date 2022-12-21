from concurrent import futures
import queue
import sys

import grpc
from numpy import empty
import queue_pb2_grpc as pb2_grpc
import queue_pb2 as pb2

from threading import Thread
from multiprocessing import Queue

class ServerHandler(pb2_grpc.ServerServicer):
    
    def __init__(self, q_size) -> None:
        super().__init__()
        # self.queue = Queue()
        self.max_q_size = int(q_size)
        # print (q_size)
        # self.peek_elem = None
        self.working_queue = []
        
    def put(self, request, context):
        try:
            request = request.message
            
            # if self.queue.empty() or self.queue._qsize() < self.max_q_size:
            if len(self.working_queue) < self.max_q_size:
                msg = "True"
                # self.queue.put(request)
                self.working_queue.append(request)
                # if self.peek_elem == None:
                #     self.peek_elem = request
                reply = {"received": True, "message": msg}
                return pb2.MessageResponse(**reply)
            
            else:
                msg = "False"
                reply = {"received": False, "message": msg}
                return pb2.MessageResponse(**reply)
        except:
            msg = "some error"
            reply = {"received": False, "message": msg}
            return pb2.MessageResponse(**reply)
    
    def peek(self, request, context):
        try:    
            # if not self.peek_elem == None:
            if len(self.working_queue) != 0:
                msg = self.working_queue[0]
                reply = {"received": True, "message": msg}
                return pb2.MessageResponse(**reply)
            
            else:
                # self.peek_elem = None
                msg = "None"
                reply = {"received": True, "message": msg}
                return pb2.MessageResponse(**reply)
        except:
            msg = "some error"
            reply = {"received": False, "message": msg}
            return pb2.MessageResponse(**reply)
    
    def pop(self, request, context):
        try:    
            # if not self.queue.empty() or self.peek_elem != None:
            if len(self.working_queue):
                msg = self.working_queue.pop(0)
                reply = {"received": True, "message": msg}
                return pb2.MessageResponse(**reply)
            
            else:
                # self.peek_elem = None
                msg = "None"
                reply = {"received": True, "message": msg}
                return pb2.MessageResponse(**reply)
        except:
            msg = "some error"
            reply = {"received": False, "message": msg}
            return pb2.MessageResponse(**reply)
    
    def size(self, request, context):
        try:
            msg = str(len(self.working_queue))
            reply = {"received": True, "message": msg}
            return pb2.MessageResponse(**reply)
        except:
            msg = "some error"
            reply = {"received": False, "message": msg}
            return pb2.MessageResponse(**reply)

def main():
    try:
        PORT = sys.argv[1]
        Q_SIZE = sys.argv[2]
    except:
        print("incorrect system arguments")
        return

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_ServerServicer_to_server(ServerHandler(Q_SIZE), server)
    server.add_insecure_port(f"127.0.0.1:{PORT}")
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Keyboard interrupt. Shutting down")
    except:
        print("Undefined error. Shutting down")


if __name__ == "__main__":
    main()