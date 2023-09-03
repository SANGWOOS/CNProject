from socket import *
from threading import Thread
from queue import Queue
import time

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))
serverSocket.setblocking(0)

print('The server is ready to receive')

rcv_base = 0  # next sequence number we wait for
que = Queue() # packet queue
que_size = 75 # queue size setting
enque_time = 0.017 # Enqueueing takes this time
deque_time = 0.023 # Dequeueing takse this time

# thread for receive and queueing
def handling_queue():
    global que
    global rcv_base
    global enque_time

    while True:
        try:
            message, clientAddress = serverSocket.recvfrom(2048)
            if str(message.decode()) == "quit":
                # 3 way handshaking
                print("client sent quit")
                break
            seq_n = int(message.decode()) # extract sequence number
            
            if que.qsize() < que_size: # queue size limit
                time.sleep(enque_time) # load to queue in delay style
                que.put(seq_n)
            
        except BlockingIOError:
            continue

# running a thread for receiving and queueing
th_handling_queue = Thread(target = handling_queue, args = ())
th_handling_queue.start()

while True:
    if que.qsize() >= 1:
        time.sleep(deque_time) # transmit delay: bandwidth emulation
        item = que.get()
        if item == rcv_base: # in order delivery
            rcv_base = item + 1
        serverSocket.sendto(str(rcv_base-1).encode(), ('127.0.0.1', 12001)) # send cumulative ack
        print("Ack: " + str(rcv_base-1), flush=True)
        if rcv_base == 1000:
            break;

th_handling_queue.join()
serverSocket.close()



