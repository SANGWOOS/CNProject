Reliable network implemented by udp socket.

# server part
1. time.sleep을 이용하여 시간지연을 발생시키고, 이를 통해 packet loss 유발
2. enque가 deque보다 더 빨리 진행 된다면 쌓이는 속도가 더 빨라서 packet이 날아감.


# client part
congestion control에 두가지 정책이 있다.
1. loss based
slow start로 처음엔 가파른 상승세 -> ssthresh 지점 부터 AIMD로 정책 변경 -> 증가 둔해짐.
이런 순서를 따르다가
triple duplicate ack: window 크기 절반으로 줄임.
timeout: window 크기 1로 줄임.
2. delay based
minimum rtt를 측정해 놓고, 이 값을 이번에 측정된 rtt로 나눈다.
0.5 이하일 시 혼잡하다고 판단해서 window 크기를 줄인다.
