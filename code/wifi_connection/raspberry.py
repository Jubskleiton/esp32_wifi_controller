from random import randint
import socket
import pickle
import threading
from time import sleep

CLIENT_ID = randint(0, 100)

HEADER = 1024
DISCONNECT_MESSAGE = "!DISCONNECT"
FORMAT = 'utf-8'
IP = "localhost" # normal -> "192.168.0.29" # Ngrok -> "localhost" get IP from cmd
PORT = 5050 # normal -> 5050 # Ngrok get from cmd
ADDR = (IP, PORT)

NICKNAME = "esp32"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

received_data_queue = []

connected = False

def send(data, head=HEADER):
    # serialize data
    message = pickle.dumps(data)
    # measure message size
    msg_len = len(message)
    # encode/serialize message length
    send_len = str(msg_len).encode(FORMAT)
    # pad length to HEADER size
    send_len += b' ' * (head - len(send_len))
    # send length
    client.send(send_len)
    # send message
    client.send(message)

def receive(head=HEADER):
    # receive message length
    msg_len = client.recv(head).decode(FORMAT)
    # veryfi connection message (effective None message)
    if msg_len:
        # receive message and deserialize
        return pickle.loads(client.recv(int(msg_len)))
    else:
        return {}

def receive_data_thread_fun(head=HEADER):
    while True:
        if not received_data_queue:
            received_data_queue.append(receive())
        elif received_data_queue and received_data_queue[0] is not None:
            data = received_data_queue[0]
            match data.get("method"):
                case "message":
                    message_sender, message_received = data.get('sender'), data.get('text')
                    print(f"{message_sender}: {message_received}")
                    received_data_queue.remove(data)
                case "clients_response":
                    print("connected_clients_num: " + data.get("connected_clients"))
                    print("connected_clients: " + f"\n  {x}" for x in data.get("connected_clients_list"))
                    received_data_queue.remove(data)
                case _:
                    print(f"{data.get('method')} method received was not expected, ignoring command")
                    received_data_queue.remove(data)


client.connect(ADDR)
connected = True
receive_data_thread = threading.Thread(target=receive_data_thread_fun, daemon=True)
receive_data_thread.start()
send({"id": CLIENT_ID, "nickname": NICKNAME})
send({"method": "get_clients"})
text = ""
print("!exit to end program")
while text != "!exit":
    text = input()
    send({"method": "message", "text": text, "selected_id" : ["all", "None"]})

sleep(1)
if connected:
    # Sending the !DISCONNECT package to server

    # serialize data
    message = pickle.dumps({"method" : f"{DISCONNECT_MESSAGE}"})
    # measure message size
    msg_len = len(message)
    # encode/serialize message length
    send_len = str(msg_len).encode(FORMAT)
    # pad length to HEADER size
    send_len += b' ' * (HEADER - len(send_len))
    # send length
    client.send(send_len)
    # send message
    client.send(message)
exit()