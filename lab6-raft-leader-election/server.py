from random import randint
import sys
from threading import Thread
import time
import queue

import grpc
from concurrent import futures

import raft_pb2 as pb2
import raft_pb2_grpc as pb2_grpc

RESTART_INTERVAL = [150, 300]
HEARTBEAT_INTERVAL = 50
NUM_MSG_THRDS = 10
TOTAL_NMB_SRVRS = 5

IP_PORT = None # get from sys


class ServerHandler(pb2_grpc.ServerServicer):
    
    def update_timer(self):
        self.timer = RESTART_INTERVAL[1]
    
    def work_follower_timer(self):
        while True:
            while self.timer:
                # countdown in intervals of 10ms
                time.sleep(10/1000)
                # server is suspended, return
                if self.is_suspended:
                    return 
                # server is a leader now, return
                if self.my_id == self.leader_id:
                    return
                self.timer = self.timer - 10
            # become a candidate under some condition
            print("The leader is dead")
            self.is_candidate = True
            if not self.become_candidate():
                self.update_timer()
    
    def work_leader_timer(self):
        while True:
            cnt = HEARTBEAT_INTERVAL
            while cnt:
                # countdown in intervals of 10ms
                time.sleep(10/1000)
                # server is suspended, return
                if self.is_suspended:
                    return 
                # someone else is a leader now, return
                if self.my_id != self.leader_id:
                    return
                cnt = cnt - 10
            # server is still a leader, now send heartbeats to everyone
            self.send_all_heartbeats()
    
    def work_vote_sender(self):
        while not self.requests_queue.empty():
            
            id = self.requests_queue.get()
            msg = pb2.PeerMessage(termNumber=self.cur_term, message=f"{self.my_id}")

            reply = self.dict_id_stub[id].RequestVote(msg)
            self.replies.append(reply)

    def become_candidate(self):
        # clear old replies
        self.replies = []
        self.cur_term = self.cur_term + 1
        self.vote_of_term = self.my_id
        print(f"I am a candidate. Term: {self.cur_term}")
        # fill the queue
        self.requests_queue = queue.Queue()
        for key in self.dict_id_stub.keys():
            if key != self.my_id:
                self.requests_queue.put(key)
        # create 10 threads that will send vote requests
        threads = []
        for i in range(NUM_MSG_THRDS):
            t = Thread(target=self.work_vote_sender)
            threads.append(t)  
            t.start()
        for t in threads:
            t.join() 
            
        num_votes = 1
        for reply in self.replies:
            if reply.received == True:
                num_votes += 1
        
        if self.is_candidate == False:
            print("Votes not received")
            return False
        
        print(f"Votes not received. Number of votes: {num_votes}")
        # become a leader
        if num_votes >= TOTAL_NMB_SRVRS//2 + 1:
            self.leader_id = self.my_id
            return True
        return False
        
    
    def work_heartbeat_sender(self):
        while not self.requests_queue.empty():
            
            id = self.requests_queue.get()
            msg = pb2.PeerMessage(termNumber=self.cur_term, message=f"{self.leader_id}")

            reply = self.dict_id_stub[id].AppendEntries(msg)
            self.replies.append(reply)
     
    def send_all_heartbeats(self):
        # clear old replies
        self.replies = []
        # fill the queue
        self.requests_queue = queue.Queue()
        for key in self.dict_id_stub.keys():
            if key != self.my_id:
                self.requests_queue.put(key)
        # create 10 threads that will send vote requests
        threads = []
        for i in range(NUM_MSG_THRDS):
            t = Thread(target=self.work_heartbeat_sender)
            threads.append(t)  
            t.start()
        for t in threads:
            t.join() 
            
        pass
        
    def waiting_func(self):    
        while not self.is_suspended:
            # is a follower
            if self.my_id != self.leader_id:
                self.timer = randint(RESTART_INTERVAL)
                
                print(f"I am a follower. Term: {self.cur_term}")
                
                self.work_follower_timer()
            # if a leader
            if self.my_id == self.leader_id:
                print(f"I am a leader. Term: {self.cur_term}")
                self.work_leader_timer()
    
    def fill_dict_of_stubs(self, dict_id_addr:dict):
        for id, ip_port in dict_id_addr.items():
            channel = grpc.insecure_channel(ip_port)
            self.dict_id_stub[id] = pb2_grpc.ServerStub(channel)
 
    def __init__(self, id, dict_id_addr):
        # dictionary of servers in the raft
        self.dict_id_stub = {}
        # my number
        self.my_id = id
        # leader number 
        self.leader_id = -1
        # current term
        self.cur_term = 1
        # for who voted on current term
        self.vote_of_term = -1
        # is suspended
        self.is_suspended = False
        
        self.is_candidate = False
        
        self.timer = self.update_timer()
        
        # waiting thread, it can 
            # request votes or  -> if follower, then become a candidate
            # send entries      -> if leader, then continue being a leader
        self.waiting_thread = Thread(target = self.waiting_func)
        
        # queue of addresses to send heartbeat and vote requests
        self.requests_queue = queue.Queue()
        
        # list of message replies from heartbeat and votes
        self.replies = []
        
        # fill the dict of stubs
        self.fill_dict_of_stubs(dict_id_addr)
        

    
    def RequestVote(self, request, context):
        """"""
        # 1. If term is equal to the term number on this server AND this server did not vote in the given term, then result is True.
        # 2. If term is greater than the term number on this server, then:
            # update its term number with the term
            # check condition 1.
        # 3. Else, the result is False
        try:
            term_num = request.termNumber
            cand_id = int(request.message)
            
            rspns = False
            
            while True:
                if self.cur_term == term_num:
                    if self.vote_of_term == -1:
                        self.vote_of_term = cand_id
                        self.leader_id = -1 # if voted for someone, then wait for a new leader
                        self.is_candidate = False # if voted for someone, then stop being a candidate
                        self.update_timer()
                        rspns = True
                    break
                elif self.cur_term < term_num:
                    self.cur_term = term_num
                    self.vote_of_term = -1
                else:
                    break
            
            rpl = {"received": rspns, "message": f"voted for {cand_id}"}
            return pb2.MessageResponse(**rpl)

        except:
            rpl = {"received": False, "message": f"failed to vote"}
            return pb2.MessageResponse(**rpl)
    
    def AppendEntries(self, request, context):
        """ Send heartbeat message
            Leader calls this function from all other servers every 50 ms
            When this function is called on the server, the server resets its timer
        """
        try:
            term_num = request.termNumber
            leader_id = int(request.message)
            
            rspns = (True if self.cur_term < term_num else False)
            self.update_timer()

            if rspns:
                rpl = {"received": rspns, "message": f"following {leader_id}"}
            else:
                rpl = {"received": rspns, "message": f"did not follow {leader_id}"}
            return pb2.MessageResponse(**rpl)

        except:
            rpl = {"received": False, "message": f"failed to append entries"}
            return pb2.MessageResponse(**rpl)
        pass
    
    def GetLeader(self, request, context):
        """Get the leader of the raft"""
        try:
            print("Command from client: getleader")
            rpl = {"received": True, "message": f"{self.leader_id}"}
            return pb2.MessageResponse(**rpl)

        except:
            rpl = {"received": False, "message": f"failed send leader"}
            return pb2.MessageResponse(**rpl)
    
    def work_suspend(self, count):
        self.is_suspended = True
        time.sleep(count) # sleep for count
        self.is_suspended = False
        pass
    
    def Suspend(self, request, context):
        """Suspend the server for requested number of seconds"""
        print(f"Command from client: suspend TODO: add time here")
        
        try:
            count = int(request.message)
            # run a new work_suspend tread
            t = Thread(target=self.work_suspend)
            t.start()
            rpl = {"received": True, "message": f"successfully suspended for {count}s"}
            return pb2.MessageResponse(**rpl)
        except:
            rpl = {"received": False, "message": f"could not suspend"}
            return pb2.MessageResponse(**rpl)
    
def main():
    try:
        ID = sys.argv[1]
        # IP_PORT = sys.argv[1]
    except:
        return
    
    dict_id_addr = {}
    file = open("Config.conf", "r")
    lines = file.readlines()
    
    for line in lines:
        line = line.split(" ")
        id = line[0]
        addr = line[1]
        dict_id_addr[id] = addr 
    
    IP_PORT = dict_id_addr[ID]
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server_handler = ServerHandler(ID)
    pb2_grpc.add_ServerServicer_to_server(server_handler, server)
    server.add_insecure_port(f"{IP_PORT}")
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("The server ends")
    except:
        print("Undefined error. Shutting down")

if __name__ == "__main__":
    main()