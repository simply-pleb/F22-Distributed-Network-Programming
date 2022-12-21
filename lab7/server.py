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
TOTAL_NMB_SRVRS = 15

IP_PORT = None 
ID = None 

dict_id_addr = {}

class Log:
    def __init__(self, index, term_number, command):
        self.index = index
        self.term_number = term_number
        self.command = command
    
    def __eq__(self, rhs):
        return self.index == rhs.index and\
            self.term_number == rhs.term_number and\
            self.command == rhs.command

class ServerHandler(pb2_grpc.ServerServicer):
    
    def update_timer(self):
        self.timer = randint(RESTART_INTERVAL[0], RESTART_INTERVAL[1])
    
    def work_follower_timer(self):
        prev_term = -2
        while True:
            while self.timer > 0:
                # countdown in intervals of 10ms
                time_to_sleed = 25
                time.sleep(time_to_sleed/1000)
                # server is suspended, return
                if self.is_suspended:
                    return 
                # server is a leader now, return
                if self.my_id == self.leader_id:
                    return
                if prev_term != self.cur_term:
                    print(f"I am a follower. Term: {self.cur_term}")
                    prev_term = self.cur_term
     
                self.timer = self.timer - time_to_sleed
            # become a candidate under some condition
            print("The leader is dead")
            self.is_candidate = True
            if not self.become_candidate():
                self.update_timer()
            else:
                return                
    
    def work_leader_timer(self):
        while True:
            cnt = HEARTBEAT_INTERVAL
            while cnt > 0:
                # countdown in intervals of 10ms
                time_to_sleed = 10
                time.sleep(time_to_sleed/1000)
                # server is suspended, return
                if self.is_suspended:
                    return 
                # someone else is a leader now, return
                if self.my_id != self.leader_id:
                    return
                cnt = cnt - time_to_sleed
            # server is still a leader, now send heartbeats to everyone
            self.send_all_heartbeats()
    
    def work_vote_sender(self):
        while not self.requests_queue.empty():
            
            id = self.requests_queue.get()
            msg = pb2.PeerRequestMessage(\
                termNumber=int(self.cur_term),\
                candidateId=int(self.my_id),\
                lastLogIndex=int(self.last_log_index),\
                lastLogTerm=int(self.last_log_term)
            )

            try:
                reply = self.dict_id_stub[id].RequestVote(msg)
                self.replies.append(reply)
            except:
                pass
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
            # print("Votes not received")
            return False
        
        # print(f"Votes received. Number of votes: {num_votes}")
        print(f"Votes received")
        # become a leader
        if num_votes >= TOTAL_NMB_SRVRS//2 + 1:
            self.leader_id = self.my_id
            return True
        return False
        
    
    def work_heartbeat_sender(self):
        while not self.requests_queue.empty():
            
            id = int(self.requests_queue.get())

            if id == self.my_id:
                continue

            prev_log_term = -1

            entry = ""

            if self.next_index[id] <= len(self.log_list):
                if self.next_index[id] - 2 >= 0:
                    prev_log_term = self.log_list[self.next_index[id] - 2].term_number    
                entry = self.log_list[self.next_index[id] - 1].command
                entry = f"{entry[0]} {entry[1]}"
                
            msg = pb2.PeerAppendMessage(\
                termNumber=int(self.cur_term),\
                leaderId=int(self.my_id),\
                prevLogIndex=int(self.next_index[id] - 1),\
                prevLogTerm=int(prev_log_term),\
                entries=entry,\
                leaderCommit=int(self.commit_index) #TODO TODO TODO
            )

            # reply = self.dict_id_stub[str(id)].AppendEntries(msg)
            # self.replies.append(reply)
                

            try:
                # print(msg)
                reply = self.dict_id_stub[str(id)].AppendEntries(msg)
                # print(f"sent heartbeat to {id}")
                self.replies.append((id, reply))
                if reply.message == "replicated":
                    # print(f"replicated {id} and new index is {self.next_index[id]}")
                    self.match_index[id] = self.next_index[id]
                    self.next_index[id] += 1
                if reply.message == "not_replicated":
                    self.next_index[id] = max(1, self.next_index[id] - 1)
                if reply.message == f"did not follow {self.my_id}":
                    self.leader_id = id

            except:
                # print(f"cannot send heartbeat to {id}")
                pass
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
        
        replicated = 0
        for key in self.dict_id_stub.keys():
            if key != self.my_id and self.match_index[int(key)] >= self.commit_index + 1:
                replicated += 1
        
        if replicated > TOTAL_NMB_SRVRS // 2:
            command = self.log_list[self.commit_index].command
            self.commit_index += 1
                
        pass
        
    def waiting_func(self):
        # print("I have started") #TO DELETE
        while not self.is_suspended:
            # is a follower
            if self.my_id != self.leader_id:
                self.timer = randint(RESTART_INTERVAL[0], RESTART_INTERVAL[1])
                # print(f"I am a follower. Term: {self.cur_term}")
                self.next_index = [self.last_log_index + 1 for i in range(TOTAL_NMB_SRVRS)]
                self.work_follower_timer()
            # if a leader
            if self.my_id == self.leader_id:
                print(f"I am a leader. Term: {self.cur_term}")
                self.work_leader_timer()
    
    def fill_dict_of_stubs(self, dict_id_addr:dict):
        for id, ip_port in dict_id_addr.items():
            
            if id == self.my_id:
                continue
            
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
        
        self.commit_index = 0
        self.last_applied = 0
        self.last_log_index = 0
        self.last_log_term = 0

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

        self.waiting_thread.daemon = True
        self.waiting_thread.start()

        self.log_list = []
        self.next_index = [1 for i in range(TOTAL_NMB_SRVRS)]
        self.match_index = [0 for i in range(TOTAL_NMB_SRVRS)]

    def RequestVote(self, request, context):
        """"""
        # 1. If term is equal to the term number on this server AND this server did not vote in the given term, then result is True.
        # 2. If term is greater than the term number on this server, then:
            # update its term number with the term
            # check condition 1.
        # 3. Else, the result is False
        
        if self.is_suspended:
            rpl = {"received": False, "message": f"is suspended"}
            return pb2.MessageResponse(**rpl)
        
        try:
            term_num = request.termNumber
            cand_id = request.candidateId
            last_log_index = request.lastLogIndex
            last_log_term = request.lastLogTerm
            
            rspns = False
            
            if term_num < self.cur_term or\
                last_log_index < self.last_log_index or\
                (self.last_log_term != last_log_term):
                rpl = {"received": False, "message": f"did not vote"}
                return pb2.MessageResponse(**rpl)

            while True:
                if self.cur_term == term_num:
                    if self.vote_of_term == -1:
                        self.vote_of_term = cand_id
                        print(f"Voted for node {cand_id}")
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
            
            if rspns:
                rpl = {"received": rspns, "message": f"voted for {cand_id}"}
            else:
                rpl = {"received": rspns, "message": f"did not vote"}
            return pb2.MessageResponse(**rpl)

        except:
            rpl = {"received": False, "message": f"failed to vote"}
            return pb2.MessageResponse(**rpl)
    
    def AppendEntries(self, request, context):
        """ Send heartbeat message
            Leader calls this function from all other servers every 50 ms
            When this function is called on the server, the server resets its timer
        """
        if self.is_suspended:
            rpl = {"received": False, "message": f"is suspended"}
            return pb2.MessageResponse(**rpl)
        
        try:
            term_num = request.termNumber
            leader_id = request.leaderId
            prev_log_index = request.prevLogIndex
            prev_log_term = request.prevLogTerm
            entries = request.entries
            leader_commit = request.leaderCommit
            
            rspns = (True if self.cur_term <= term_num else False)

            if self.cur_term < term_num:
                self.cur_term = term_num
                # print(f"I am a follower. Term: {self.cur_term}")
            
            if rspns:
                # self.update_timer()
                self.timer = RESTART_INTERVAL[1]
                self.leader_id = leader_id
                
                if entries != "":
                    command = tuple(entries.split(" "))
                    cur_log = Log(prev_log_index + 1, term_num, command)
                    if len(self.log_list) == 0:
                        self.log_list.append(cur_log)
                        rpl = {"received": rspns, "message": f"replicated"}
                    elif prev_log_index == 0:
                        if self.log_list[0] != cur_log:
                            self.log_list = [cur_log]
                        rpl = {"received": rspns, "message": f"replicated"}
                    elif self.log_list[prev_log_index-1].term_number == prev_log_term:
                        if len(self.log_list) == prev_log_index:
                            self.log_list.append(cur_log)
                        else:
                            if self.log_list[prev_log_index] != cur_log:
                                self.log_list = self.log_list[:prev_log_index:]
                                self.log_list.append(cur_log)

                        rpl = {"received": rspns, "message": f"replicated"}
                    else:
                        rpl = {"received": rspns, "message": f"not_replicated"}
                else:
                    rpl = {"received": rspns, "message": f"no_entry"}
            else:
                rpl = {"received": rspns, "message": f"did not follow {leader_id}"}
            
            if len(self.log_list) != 0:
                self.last_log_index = self.log_list[-1].index
                self.last_log_term = self.log_list[-1].term_number

            # if leader_commit > self.commit_index and rpl["message"] == "replicated":
            #     self.commit_index = min(prev_log_index + 1, leader_commit)

            self.commit_index = self.last_log_index
        
            # print("!!!!!!!")
        
            return pb2.MessageResponse(**rpl)

        except:
            # print("heartbeat went wrong")
            rpl = {"received": False, "message": f"failed to append entries"}
            return pb2.MessageResponse(**rpl)
        pass
    
    def GetLeader(self, request, context):
        """Get the leader of the raft"""
        
        if self.is_suspended:
            rpl = {"received": False, "message": f"is suspended"}
            return pb2.MessageResponse(**rpl)
        
        try:
            # print(self.leader_id, dict_id_addr[self.leader_id])
            msg = str(self.leader_id) + " " + str(dict_id_addr.get(str(self.leader_id)))
            print("Command from client: getleader")
            print(msg)
            rpl = {"received": True, "message": f"{msg}"}
            return pb2.MessageResponse(**rpl)

        except:
            rpl = {"received": False, "message": f"failed send leader"}
            return pb2.MessageResponse(**rpl)
    
    def work_suspend(self, count):
        print(f"Sleeping for {count} seconds")
        self.is_suspended = True
        time.sleep(count) # sleep for count
        self.is_suspended = False
        pass
    
    def Suspend(self, request, context):
        """Suspend the server for requested number of seconds"""
        
        try:
            if self.is_suspended:
                rpl = {"received": False, "message": f"is suspended"}
                return pb2.MessageResponse(**rpl)
            
            count = int(request.message)
            print(f"Command from client: suspend {count}")
            # run a new work_suspend tread
            t = Thread(target=self.work_suspend, kwargs={'count': count})
            t.start()
            rpl = {"received": True, "message": f"successfully suspended for {count}s"}
            return pb2.MessageResponse(**rpl)
        except:
            rpl = {"received": False, "message": f"could not suspend"}
            return pb2.MessageResponse(**rpl)
    
    def SetVal(self, request, context):
        if self.is_suspended:
            rpl = {"received": False, "message": f"is suspended"}
            return pb2.MessageResponse(**rpl)
        
        if self.leader_id == -1:
            rpl = {"received": False, "message": f"currently we don't have leader"}
            return pb2.MessageResponse(**rpl)
        
        if self.my_id != self.leader_id:
            return self.dict_id_stub[str(self.leader_id)].SetVal(request)

        self.log_list.append(Log(\
            index=len(self.log_list)+1,\
            term_number=self.cur_term,\
            command=(request.key, request.value)
        ))

        self.last_log_index = len(self.log_list)
        self.last_log_term = self.cur_term
        rpl = {"received": True, "message": f"new command: set value of {request.key} to {request.value}"}
        return pb2.MessageResponse(**rpl)

    def GetVal(self, request, context):
        res = "None"
        # print("LOGS:")
        # for log in self.log_list:
        #     print(log.index, log.term_number, log.command)
        # print("Nexts and matchindexes:")
        # for i in range(TOTAL_NMB_SRVRS):
        #     print(f"index= {i} - next= {self.next_index[i]} match= {self.match_index[i]}")
        # print(f"Commit index: {self.commit_index}")
        # print(f"last index= {self.last_log_index} <-> last term= {self.last_log_term}")
        
        for log in self.log_list[:self.commit_index:]:
            if request.key == log.command[0]:
                res = log.command[1]
        rpl = {"received": True, "message": f"{res}"}
        return pb2.MessageResponse(**rpl)
    
def main():
    global TOTAL_NMB_SRVRS
    try:
        ID = sys.argv[1]
        # IP_PORT = sys.argv[1]
    except:
        return
    
    file = open("Config.conf", "r")
    lines = file.readlines()
    TOTAL_NMB_SRVRS = len(lines)
    file.close()
    
    for line in lines:
        line = line.split(" ")
        id = line[0]
        addr = (line[1] + ":" + line[2]).replace('\n', '')
        dict_id_addr[id] = addr 

    # print(dict_id_addr)
    
    IP_PORT = dict_id_addr[ID]
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server_handler = ServerHandler(ID, dict_id_addr)
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
