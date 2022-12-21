from cmath import sqrt
import math
import socket
import sys

from threading import Thread
from time import sleep

PORT = int(sys.argv[1])
TCP_IP = '127.0.0.1'
BUFFER_SIZE = 1024

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind((TCP_IP, PORT))
soc.listen()
# soc.setblocking(False)
# soc.settimeout(WAIT_TIME)

dict_con_name = {}

def send_names_to_all():
    conns = dict_con_name.keys
    names = dict_con_name.values
    for conn in conns:
        conn.sendall(str(names))
    pass

def worker_track_is_conn(conn):
    while True:
        try:
            conn.sendall("are you alive?")
            sleep(1)
        except:
            # recreate the socket and reconnect
            dict_con_name.pop(conn)

while True:
    soc.accept
    conn, addr = soc.accept()  
    rcv = conn.recv()
    dict_con_name[conn] = rcv
    send_names_to_all()
    th = Thread(target=worker_track_is_conn, args=(conn))
    th.start()
