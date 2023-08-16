from random import randint
import flet as ft
import socket
import pickle
import threading


CLIENT_ID = randint(0, 100)


HEADER = 1024
PORT = 5050 # normal -> 5050 # Ngrok get from cmd
DISCONNECT_MESSAGE = "!DISCONNECT"
FORMAT = 'utf-8'
IP = "localhost" # normal -> "192.168.0.29" # Ngrok get from cmd
ADDR = (IP, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

received_data_queue = []

connected = False


def main(page: ft.Page):
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
                    case "clients_response":
                        clients_dropdown.options.clear()
                        clients_dropdown.options.append(ft.dropdown.Option("Send to all"))
                        for i in data.get("connected_clients_list"):
                            clients_dropdown.options.append(ft.dropdown.Option(f"Nickname: {i[1]}\nID: {i[0]}"))
                        page.update()
                        received_data_queue.remove(data)
                    case "file":
                        print(f"received file")
                        file_contents = data.get("file")
                        with open(f'received_file.{data.get("file_extension")}', 'wb') as file:
                            file.write(file_contents)
                        print("file saved as received_file")
                        received_data_queue.remove(data)
                    case "message":
                        messages_list.pop(1)
                        messages_list.append(ft.Text(f"{data.get('sender')}: {data.get('text')}", color="#aaaaaa"))
                        page.update()
                        received_data_queue.remove(data)
                    case _:
                        print(data)

    def on_start_config_button_click(e):
        global IP
        global PORT
        global ADDR
        if ip_port_input_field.value:
            IP, PORT = ip_port_input_field.value.split(":")
            ADDR = (IP, PORT)
        if nickname_input_field.value:
            global client
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR)
            global connected
            connected = True
            receive_data_thread = threading.Thread(target=receive_data_thread_fun, daemon=True)
            receive_data_thread.start()
            send({"id": CLIENT_ID, "nickname": nickname_input_field.value})
            nickname.clear()
            nickname.append(nickname_input_field.value)
            send({"method": "get_clients"})
            close_dlg(e)


    def on_refresh_online_clients_button_click(e):
        send({"method": "get_clients"})

    def on_set_destination_button_click(e):
        if clients_dropdown.value == "Send to all" or clients_dropdown.value is None:
            selected_id.clear()
            selected_id.append("all")
            selected_id.append("None")
        else:
            selected_id.clear()
            selected_id.append(clients_dropdown.value.split("\nID: ")[0].split(": ")[1])
            selected_id.append(clients_dropdown.value.split("\nID: ")[1])
        message_send_button.text = f"Send to {selected_id[0]}"
        page.update()
        print(selected_id)

    def on_file_pick(e: ft.FilePickerResultEvent):
        file_path_text.value = e.files[0].path
        page.update()
        selected_file_path.clear()
        selected_file_path.append(e.files[0].path)

    def close_dlg(e):
        file_alert_popup.open = False
        if nickname_popup:
            page.title = f"Nickname: {nickname[0]} - ID: {CLIENT_ID}"
            page.update()
        nickname_popup.open = False
        page.update()

    def on_send_file_button(e):
        if selected_file_path:
            print("sending file")
            with open(selected_file_path[0], 'rb') as file:
                file_data = file.read()
            send({"method": "file", "file_extension": selected_file_path[0].split(".")[-1], "file": file_data, "selected_id": selected_id})
        else:
            page.dialog = file_alert_popup
            file_alert_popup.open = True
            page.update()


    # main page
    # selected direct message client
    selected_id = ["all", "None"]
    # Message input field
    message_input_field = ft.TextField(label="Message input")
    # Message send button
    message_send_button = ft.ElevatedButton(text="Send to all", on_click=lambda x: send({"method": "message", "text": message_input_field.value, "selected_id" : selected_id}))
    # Direct message button
    get_online_clients_button = ft.ElevatedButton(text="Refresh online clients", on_click=on_refresh_online_clients_button_click)
    # Grid os Online clients
    clients_dropdown = ft.Dropdown(width=200, options=[])
    # set message destination button
    set_client_destination_button = ft.ElevatedButton(text="Set destination message", on_click=on_set_destination_button_click)
    # Select file button
    file_picker = ft.FilePicker(on_result=on_file_pick)
    page.overlay.append(file_picker)
    page.update()
    file_picker_button = ft.ElevatedButton("Select file", on_click=lambda _: file_picker.pick_files(allow_multiple=False))
    # file path show text
    file_path_text = ft.Text("")
    # Send file button
    file_send_button = ft.ElevatedButton("Send file", on_click=on_send_file_button)
    # Selected file
    selected_file_path = []
    # no file selected alert popup
    file_alert_popup = ft.AlertDialog(
        modal=True,
        title=ft.Text("No file selected"),
        content=ft.Text("Select a file before trying to send"),
        actions=[
            ft.TextButton("ok", on_click=close_dlg)
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    # Set Nickname popup
    ip_port_input_field = ft.TextField(label="IP:PORT")
    nickname_input_field = ft.TextField(label="Nickname")
    start_config_button = ft.ElevatedButton(text="Confirm", on_click=on_start_config_button_click)

    nickname_popup = ft.AlertDialog(
        modal=True,
        title=ft.Text("Select nickname"),
        actions=[
            ip_port_input_field,
            nickname_input_field,
            start_config_button
        ]
    )

    messages_list = [ft.Text("Messages"), ft.Text(), ft.Text(), ft.Text(), ft.Text(), ft.Text(), ft.Text(), ft.Text(), ft.Text(), ft.Text(), ft.Text()]

    nickname = [""]

    # Main page layout
    page.add(ft.Row(controls=[
        ft.Column(controls=[
            ft.Row(controls=[message_input_field,
                             message_send_button
                             ]),
            get_online_clients_button,
            ft.Row(controls=[
                clients_dropdown,
                set_client_destination_button
            ]),
            ft.Row(controls=[
                file_picker_button,
                file_path_text
            ]),
            ft.Row(controls=[
                file_send_button
            ])
        ], alignment=ft.alignment.top_left),
        ft.Column(controls=
                  messages_list
                  )
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START))

    page.dialog = nickname_popup
    nickname_popup.open = True
    page.update()

ft.app(target=main)


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

