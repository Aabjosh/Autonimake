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

HOST = '0.0.0.0' # listen on 'all network interfaces'
PORT = 8000 # recieve messages on this port

wifi_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # creates an object to get messages, where the regular internet protocol is the type and the method of retrieval is the TCP protocol
wifi_server.bind((HOST, PORT)) # make sure the port to listen on and the host IP are configured
wifi_server.listen() # begin listening

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # goes up one folder
PERIPHERALS_PATH = os.path.join(SCRIPT_DIR, "peripherals.json")

if os.path.exists(PERIPHERALS_PATH):
    with open(PERIPHERALS_PATH, "r") as f:
        std_peripherals = json.load(f).get("standard", {})
else:
    print("peripherals.json not found, using defaults.")

found_devices = {}

# start by getting all USB serial ports with devices on them
for port in ports:
    for port in ports:
        monitor = None
        try:
            monitor = serial.Serial(port, 115200, timeout=2)
            monitor.setDTR(False)
            time.sleep(0.1)
            monitor.setDTR(True)
            time.sleep(2)

            id = ""
            for _ in range(20):  # read up to 20 lines
                line = monitor.readline().decode(errors='ignore').strip()
                if line in std_peripherals:
                    id = line
                    break

            if id:
                found_devices[id] = monitor
                print(f"Found: {id}")
            else:
                print("ID not found in boot output")
                monitor.close()
        except Exception as e:
            import traceback
            traceback.print_exc()
            if monitor:
                monitor.close()

print(f"got {len(found_devices.keys())} port peripherals")

while True:
    connection, address = wifi_server.accept()
    print(f"Connected from {address}")
    with connection:
        while True:
            message = connection.recv(1024).decode().strip()
            if not message:
                break
            
            message_list = message.split(",")
            if len(message_list) < 2:
                continue

            target = message_list[0]
            command = message_list[1]

            if target not in found_devices:
                continue

            tx = found_devices[target]
            data_type = std_peripherals[target]
            data_string = UART_m.getMessage(data_type, command)
            tx.write(data_string.encode())
            print(f"SENT: {data_string} TO: {tx}")