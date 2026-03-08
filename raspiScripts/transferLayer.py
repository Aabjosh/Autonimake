# This file takes care of sending messages over to the devices from the hub, as recieved from computer's packets
import socket # manages comms with the computer
import serial # UART protocol
import time # timeouts
import glob # global instance search for the usb thingies
import os
import json

# functions for easy mgmt
import standardUARTMessages as UART_m

ports = glob.glob('/dev/ttyUSB*') # only care about usb uart

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # goes up one folder
PERIPHERALS_PATH = os.path.join(SCRIPT_DIR, "peripherals.json")

if os.path.exists(PERIPHERALS_PATH):
    with open(PERIPHERALS_PATH, "r") as f:
        std_peripherals = json.load(f).get("standard", PERIPHERALS_PATH)
else:
    print("peripherals.json not found, using defaults.")

found_devices = {}

# start by getting all USB serial ports with devices on them
for port in ports:
    try:
        monitor = serial.Serial(port, 115200, timeout=2) # establishable?
        time.sleep(2)
        id = monitor.readline().decode().strip() # check the Peripheral ID

        if id in std_peripherals: # if the peripheral ID is a key for the standard peripherals, then add it as a key for this monitor object in the dict
            found_devices[id] = monitor
        else:
            monitor.close()
    except:
        print("error finding port")

print(f"got {found_devices.keys().__len__} port peripherals")


serial_1 = serial.Serial("/dev/serial0", 115200, timeout=1) # MIGHT WANNA REMOVE THHIS TIMEOUT!
time.sleep(2) # lets the UART become stable

HOST = '0.0.0.0' # listen on 'all network interfaces'
PORT = 8000 # recieve messages on this port

wifi_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # creates an object to get messages, where the regular internet protocol is the type and the method of retrieval is the TCP protocol

wifi_server.bind(HOST, PORT) # make sure the port to listen on and the host IP are configured

wifi_server.listen() # begin listening

while True:
    message_list = []
    target = ""
    command = ""

    connection, address = wifi_server.accept()

    with connection:
        message = connection.recv(1024).decode().strip() # takes at max 1024 chars from the packet and parses it, cuts whitespace
        if message:

            # to store the two parts of the message
            message_list = message.split(" ")
            
            # if bad message from computer, ignore
            if len(message_list) < 2:
                continue

            # first element of the message is the device ID, second is the actual command
            target = message_list[0]
            command = message_list[1]

            # if target UART DNE, ignore
            if target not in found_devices:
                continue

            tx = found_devices[target] # get the UART port to send to
            data_type = std_peripherals[target] # get the string name for the type of message to send given the peripheral
            data_string = UART_m.getMessage(target, command) # get the actual string to send

            tx.write(data_string.encode())