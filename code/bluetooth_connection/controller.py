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
    while True:
        method = input("1: Send log message\n2: Set RGB\3e: Exit\nWhat to do: ")
        match  method:
            case "1":
                send({"method":"log", "log":input("log: ")}, conn)
            case "2":
                send({"method":"RGB", "R":input("R: "), "G":input("G: "), "B":input("B: ")}, conn)
            case "e":
                send({"method": DISCONNECT_MESSAGE}, conn)
                exit()


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
    print(f"{nickname} initialized")
else:
    print("Error wrong method send on initialization")
    conn.close()
    exit()

thread = threading.Thread(target=terminal_input, args=(), daemon=True)
thread.start()

while True:
    data = receive(conn)
    if data:
        if data.get("method") == DISCONNECT_MESSAGE:
            print(f"{nickname} Disconnected, stopping program")
            break
        else:
            if data.get("method") == "log":
                print(f"[{nickname}] {data.get('log')}")
            elif data.get("method") == "func":
                if data.get("func") == "battery level":
                    print(f"{data.get('batlvl')}")
                    # changing code based on power level
            else:
                print(f"[{nickname}:{conn}] {data}")


conn.close()
controller.close()
print("exited")
exit()
