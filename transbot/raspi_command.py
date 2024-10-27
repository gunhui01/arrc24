#!/usr/bin/env python3

__author__ = "Park Gunhui"

import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc):
	if rc == 0: print("Connected success")
	else: print("Bad connection returned code: ", rc)

def on_publish(client, userdata, mid):
	print(f"Message published. MID: {mid}")

def raspi_command(command_queue):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.connect("192.168.0.2", 1883, 60)

    while True:
        if not command_queue.empty():
            command = command_queue.get()
            client.publish("jetson/command", command)