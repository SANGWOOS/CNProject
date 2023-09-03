from socket import *
from threading import Thread
import random
import time
import math

serverIP = '127.0.0.1' # special IP for local host
serverPort = 12000
clientPort = 12001

win = 1.0     # window size
no_pkt = 1000 # the total number of packets to send
send_base = 0 # oldest packet sent
seq = 0        # initial sequence number
timeout_flag = 0 # timeout trigger
triple_flag = False # fast retransmission trigger
final_flag = False # chk ack == 999?

ack_count = [0 for i in range(2000)] # counting ack number
sent_time = [0 for i in range(2000)] # sent time
triple_times = 0 # How many times triple ack occur?
timeout_times = 0 # How many times timeout occur?


clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.bind(('', clientPort))
clientSocket.setblocking(0)

# thread for receiving and handling acks: loss based
def handling_ack_loss():
    print("thread")
    global clientSocket
    global send_base
    global timeout_flag
    global sent_time
    global ack_count
    global triple_flag
    global win
    global final_flag

    alpha = 0.125
    beta = 0.25
    timeout_interval = 10  # timeout interval
    ssthresh = no_pkt

    estimated_rtt = 0
    pkt_delay = 0
    dev_rtt = 0
    init_rtt_flag = 1
    
    while True:
       
        if sent_time[send_base] != 0: 
            pkt_delay = time.time() - sent_time[send_base]
     
            
        if pkt_delay > timeout_interval and timeout_flag == 0:    # timeout detected
            print("timeout detected:", str(send_base), flush=True)
            print("timeout interval:", str(timeout_interval), flush=True)
            timeout_flag = 1
            ssthresh = win / 2.0
            win = 1
            

        try:
            ack, serverAddress = clientSocket.recvfrom(2048)
            ack_n = int(ack.decode())
            print(ack_n, flush=True)
            ack_count[ack_n] += 1

            if ack_count[ack_n] == 3: # triple duplicated ack
                ack_count[ack_n] = 0
                triple_flag = True
                win /= 2.0
                if win < 1.0:
                    win = 1.0
                continue
            
            if init_rtt_flag == 1:
                estimated_rtt = pkt_delay
                init_rtt_flag = 0
            else:
                estimated_rtt = (1-alpha)*estimated_rtt + alpha*pkt_delay
                dev_rtt = (1-beta)*dev_rtt + beta*abs(pkt_delay-estimated_rtt)
            timeout_interval = estimated_rtt + 4*dev_rtt
            #print("timeout interval:", str(timeout_interval), flush=True)
            
        except BlockingIOError:
            continue
            
        # window is moved upon receiving a new ack
        # window stays for cumulative ack
        '''if ack_count[send_base] == 1:
            print(win)'''
        send_base = ack_n + 1
        if ssthresh > win:
            win += 1.0
        else:
            win += 1.0 / math.floor(win)
        if ack_n == 999:
            final_flag = True
            break;


# thread for receiving and handling acks: delay based
def handling_ack_delay():
    print("thread")
    global clientSocket
    global send_base
    global timeout_flag
    global sent_time
    global ack_count
    global triple_flag
    global win
    global final_flag

    alpha = 0.125
    beta = 0.25
    timeout_interval = 10  # timeout interval
    similarity = 0.5
    min_rtt = 0.0
    delay_flag = False

    estimated_rtt = 0
    pkt_delay = 0
    dev_rtt = 0
    init_rtt_flag = 1
    
    while True:
       
        if sent_time[send_base] != 0: 
            pkt_delay = time.time() - sent_time[send_base]
     
            
        if pkt_delay > timeout_interval and timeout_flag == 0:    # timeout detected
            print("timeout detected:", str(send_base), flush=True)
            print("timeout interval:", str(timeout_interval), flush=True)
            timeout_flag = 1
            win = 1.0

        try:
            ack, serverAddress = clientSocket.recvfrom(2048)
            ack_n = int(ack.decode())
            print(ack_n, flush=True)
            ack_count[ack_n] += 1

            if ack_count[ack_n] == 3: # triple duplicated ack
                ack_count[ack_n] = 0
                triple_flag = True
                win = win / 2
                if win < 1.0:
                    win = 1.0
                continue
            
            if init_rtt_flag == 1:
                estimated_rtt = pkt_delay
                min_rtt = estimated_rtt
                init_rtt_flag = 0
            else:
                estimated_rtt = (1-alpha)*estimated_rtt + alpha*pkt_delay
                dev_rtt = (1-beta)*dev_rtt + beta*abs(pkt_delay-estimated_rtt)
            timeout_interval = estimated_rtt + 4*dev_rtt
            #print("timeout interval:", str(timeout_interval), flush=True)
            if (min_rtt / estimated_rtt) < similarity:
                delay_flag = True
            if min_rtt > estimated_rtt:
                min_rtt = estimated_rtt
            
        except BlockingIOError:
            continue
            
        # window is moved upon receiving a new ack
        # window stays for cumulative ack
        '''if ack_count[send_base] == 1:
            print(win)'''
        send_base = ack_n + 1
        if ack_n == 999: # end condition
            final_flag = True
            break;
        if delay_flag == False: # un congested
            win += 1 / math.floor(win)
        else: # congested
            win -= 1 / math.floor(win)
            if win < 1:
                win = 1
        delay_flag = False

        if ack_n % 50 == 0:
            min_rtt = estimated_rtt


mode = int(input('mode: 1) loss based / 2) delay based\n'))
start = time.time()
if mode == 1:
    # running a thread for receiving and handling acks
    th_handling_ack = Thread(target = handling_ack_loss, args = ())
    th_handling_ack.start()

    while send_base < no_pkt:
        while seq < send_base + win: # send packets within window
            clientSocket.sendto(str(seq).encode(), (serverIP, serverPort))  
            sent_time[seq] = time.time()    
            seq = seq + 1

        if timeout_flag == 1: # retransmission -> timeout
            seq = send_base 
            clientSocket.sendto(str(seq).encode(), (serverIP, serverPort))
            sent_time[seq] = time.time()
            print("timeout retransmission: " + str(seq), flush=True)
            seq = seq + 1
            timeout_times += 1
            timeout_flag = 0

        if triple_flag == True: # retransmission -> triple duplicate ack
            clientSocket.sendto(str(send_base).encode(), (serverIP, serverPort))
            sent_time[send_base] = time.time()
            print("triple Ack retransmission: " + str(send_base - 1), flush=True)
            triple_times += 1
            triple_flag = False

    th_handling_ack.join() # terminating thread

    if final_flag == True:
        # for 3 way handshaking
        clientSocket.sendto("quit".encode(), (serverIP, serverPort))
        final_flag = False

    print ("done")
    clientSocket.close()
elif mode == 2:
    # running a thread for receiving and handling acks
    th_handling_ack = Thread(target = handling_ack_delay, args = ())
    th_handling_ack.start()

    while send_base < no_pkt:
        while seq < send_base + win: # send packets within window
            clientSocket.sendto(str(seq).encode(), (serverIP, serverPort))  
            sent_time[seq] = time.time()    
            seq = seq + 1

        if timeout_flag == 1: # retransmission -> timeout
            seq = send_base 
            clientSocket.sendto(str(seq).encode(), (serverIP, serverPort))
            sent_time[seq] = time.time()
            print("timeout retransmission: " + str(seq), flush=True)
            seq = seq + 1
            timeout_times += 1
            timeout_flag = 0

        if triple_flag == True: # retransmission -> triple duplicate ack
            clientSocket.sendto(str(send_base).encode(), (serverIP, serverPort))
            sent_time[send_base] = time.time()
            print("triple Ack retransmission: " + str(send_base - 1), flush=True)
            triple_times += 1
            triple_flag = False

    th_handling_ack.join() # terminating thread

    if final_flag == True:
        # for 3 way handshaking
        clientSocket.sendto("quit".encode(), (serverIP, serverPort))
        final_flag = False

    print ("done")
    clientSocket.close()
else:
    print('mode error')
print('elapsed time: ' + str(time.time() - start))
print('triple ack : ' + str(triple_times))
print('timeout : ' + str(timeout_times))


