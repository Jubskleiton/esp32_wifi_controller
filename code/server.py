import socket
import threading
import pickle


HEADER = 1024
PORT = 5050
IP = "localhost" # normal -> socket.gethostbyname(socket.gethostname())  #WEB -> Meu IP Publico "179.154.203.251" # Ngrock -> "localhost"
ADDR = (IP, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

connected_list = {}

def terminal_input():
    pass

def handle_client(conn, addr, client_id):
    print(f"{addr} connected")
    connected = True
    while connected:
        data = receive(conn)
        if data:
            if data.get("method") == DISCONNECT_MESSAGE:
                print(f"{connected_list.get(client_id).get('nickname'), client_id} Disconnecting")
                connected_list.pop(client_id)
                connected = False
            else:
                if data.get("method") == "file":
                    print(f"{connected_list.get(client_id).get('nickname'), client_id} requested to send file to {connected_list.get(int(data.get('selected_id')[1])).get('nickname'), data.get('selected_id')[1]}")
                    if data.get("selected_id")[1]:
                        print(f"sending file to {data.get('selected_id')[0]}")
                        data.update({"sender": connected_list.get(client_id).get("nickname")})
                        send(data, connected_list.get(int(data.get("selected_id")[1])).get("conn"))
                elif data.get("method") == "message":
                    print(f"[{client_id, connected_list.get(client_id).get('nickname')}: Message to {data.get('selected_id')}] {data.get('text')}")
                    if data.get("selected_id")[0] == "all":
                        for client in connected_list.keys():
                            send({"method" : "message", "text" : data.get("text"), "sender" : connected_list.get(client_id).get("nickname")}, connected_list.get(client).get("conn"))
                    else:
                        send({"method" : "message", "text" : data.get("text"), "sender" : connected_list.get(client_id).get("nickname")}, connected_list.get(int(data.get("selected_id")[1])).get("conn"))
                elif data.get("method") == "get_clients":
                    print(f"{client_id, connected_list.get(client_id).get('nickname')} requested Online clients")
                    data = {"method" : "clients_response", "connected_clients" : str(threading.active_count() - 1), "connected_clients_list" : [(i, connected_list.get(i).get("nickname")) for i in connected_list.keys()]}
                    send(data, conn)
                else:
                    print(f"[{addr}] {data}")

    conn.close()

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


def start():
    server.listen()
    #subprocess.call(["C:/Users/enzog/Área de Trabalho/ngrok.exe", "tcp", "--domain=rd_2RivBLUuGwnWdFeVmAASbquCBmT", "{PORT}"])
    print(f"[LISTENING] server up on {IP}")
    while True:
        conn, addr = server.accept()
        client_data = receive(conn)
        if client_data.get("id"):
            client_id = client_data.get("id")
            client_nickname = client_data.get("nickname")
            thread = threading.Thread(target=handle_client, args=(conn, addr, client_id))
            thread.start()
            connected_list.update({client_id : {"conn" : conn, "addr" : addr, "nickname" : client_nickname}})
            print(f"[{threading.active_count() - 1} Clients connected] New client connected")
            print(connected_list)
        elif client_data.get("download"):
            print("received download client request")
            with open("client.exe", 'rb') as file:
                file_data = file.read()
            print(f"sending client to [{conn} : {addr}]")
            send({"file" : file_data}, conn)
            print(f"closing connection with [{conn} : {addr}]")
            conn.close()
print("Starting server")
start()
print(connected_list)