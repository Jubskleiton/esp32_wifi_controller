import socket
import threading
import pickle


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
    # encode/serialize message length
    send_len = str(msg_len).encode(FORMAT)
    # pad length to HEADER size
    send_len += b' ' * (head - len(send_len))
    # send length
    conn.send(send_len)
    # send message
    conn.send(message)


def receive(conn, head=HEADER):
    # receive message length
    msg_len = conn.recv(head).decode(FORMAT)
    # veryfi connection message (effective None message)
    if msg_len:
        # receive message and deserialize
        return pickle.loads(conn.recv(int(msg_len)))
    else:
        return {}

controller = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
controller.bind(ADDR)

controller.listen()
print(f"LISTENING up on {MAC_ADDRESS}")
conn, addr = controller.accept()
print(f"{addr} connected")
print("initialing for " + addr)
data = receive(conn)
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
    if input("send log message ? Y/n").upper() == "Y":
        send({"method":"message", "text":input("text: ")}, conn)
    else:
        print("rgb led method")
        send({"method":"LED RGB", "LED Red":input("R: "), "LED Green":input("G: "), "LED Blue":input("B: ")}, conn)

send({"method":DISCONNECT_MESSAGE}, conn)
conn.close()
exit()