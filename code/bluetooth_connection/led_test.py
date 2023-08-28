# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple test for NeoPixels on Raspberry Pi
import time
import board
import neopixel
from random import randint
import socket
import pickle
import threading
from time import sleep

CLIENT_ID = randint(0, 100)

HEADER = 1024
DISCONNECT_MESSAGE = "!DISCONNECT"
FORMAT = 'utf-8'
MAC_ADDRESS = "b4:8c:9d:5b:7d:ee" #
CHANNEL = 4 # 1 - 20
ADDR = (MAC_ADDRESS, CHANNEL)

NICKNAME = "Raspberry"

wait = 1

cycle_wheel = True

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 33

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.RGB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER
)


def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0)


def rainbow_cycle():
    if cycle_wheel:
        for j in range(255):
            for i in range(num_pixels):
                pixel_index = (i * 256 // num_pixels) + j
                pixels[i] = wheel(pixel_index & 255)
            pixels.show()
            time.sleep(wait)


def send(data, head=HEADER):
    # serialize data
    message = pickle.dumps(data)
    # measure message size
    msg_len = len(message)
    print(msg_len)
    # convert message length to bytes
    send_len = msg_len.to_bytes(head, byteorder='big')
    # send length
    client.send(send_len)
    # send message
    client.send(message)

def receive(head=HEADER):
    # receive message length
    send_len = client.recv(head)
    msg_len = int.from_bytes(send_len, byteorder='big')
    # verify connection message (effectively None message)
    if msg_len:
        # receive message and deserialize
        return pickle.loads(client.recv(msg_len))
    else:
        return {}

def terminal_input():
    while True:
        method = input("1: Send log message\n2: Send power level\3e: Exit\nWhat to do: ")
        match  method:
            case "1":
                send({"method":"log", "log":input("log: ")})
            case "2":
                send({"method":"RGB", "R":input("R: "), "G":input("G: "), "B":input("B: ")})
            case "e":
                send({"method": DISCONNECT_MESSAGE})
                exit()


client = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

print("reaching to connect")
client.connect(ADDR)
print("connected")
print("initializing")
sleep(1)
receive_data_thread = threading.Thread(target=terminal_input, daemon=True)
receive_data_thread.start()

wheel_thread = threading.Thread(target=wheel, args=(), daemon=True)

send({"nickname": NICKNAME})


while True:
    data = receive()
    if data.get("method") == DISCONNECT_MESSAGE:
        break
    else:
        if data.get("method") == "message":
            if data.get("log") == "wheel":
                cycle_wheel = not cycle_wheel
            print(data.get("log"))
        elif data.get("method") == "RGB":
            if data.get("R").isnumeric() and data.get("G").isnumeric and data.get("B").isnumeric:
                pixels.fill((int(data.get("R")), int(data.get("G")), int(data.get("B"))))
                pixels.show()
        else:
            print(f"{data.get('method')} method received was not expected, ignoring command")


client.close()
print("exited")
exit()