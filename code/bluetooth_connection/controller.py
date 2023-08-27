import socket
import threading
import pickle
from time import sleep

HEADER = 1024
CHANNEL = 4 # 1 - 20
MAC_ADDRESS = "b4:8c:9d:5b:7d:ee"
ADDR = (MAC_ADDRESS, CHANNEL)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"


def terminal_input():
    pass

def handle_received(conn, addr, nickname):
    while True:
        data = receive(conn)
        if data:
            if data.get("method") == DISCONNECT_MESSAGE:
                print(f"{nickname} Disconnecting")
                conn.close()
                controller.close()
                exit()
            else:
                if data.get("method") == "message":
                    print(f"[{nickname}] {data.get('text')}")
                elif data.get("method") == "func":
                    if data.get("func") == "battery level":
                        print(f"{data.get('batlvl')}")
                        # changing code based on power level
                else:
                    print(f"[{addr}] {data}")



def send(data, conn, head=HEADER):
    # serialize data
    message = pickle.dumps(data)
    # measure message size
    msg_len = len(message)
    print(msg_len)
    # convert message length to bytes
    send_len = msg_len.to_bytes(head, byteorder='big')
    # send length
    conn.send(send_len)
    # send message
    conn.send(message)

def receive(conn, head=HEADER):
    # receive message length
    send_len = conn.recv(head)
    msg_len = int.from_bytes(send_len, byteorder='big')
    # verify connection message (effectively None message)
    if msg_len:
        # receive message and deserialize
        return pickle.loads(conn.recv(msg_len))
    else:
        return {}


controller = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
controller.bind(ADDR)

controller.listen()
print(f"LISTENING up on {MAC_ADDRESS}")
conn, addr = controller.accept()
print(f"{addr} connected")
print("initialing for " + str(addr))
receive(conn)
data = receive(conn)
print(data)
if data.get("nickname"):
    nickname = data.get("nickname")
    thread = threading.Thread(target=handle_received, args=(conn, addr, nickname))
    thread.start()
    print(f"{nickname} initialized")
else:
    print("Error wrong method send on initialization")
    conn.close()
    exit()

while True:
    if input("quit ? Y/n: ").upper() == "Y":
        break
    if input("send log message ? Y/n: ").upper() == "Y":
        send({"method":"message", "text":input("text: ")}, conn)
    else:
        print("rgb led method")
        send({"method":"LED RGB", "LED Red":input("R: "), "LED Green":input("G: "), "LED Blue":input("B: ")}, conn)

send({"method":DISCONNECT_MESSAGE}, conn)
conn.close()
exit()