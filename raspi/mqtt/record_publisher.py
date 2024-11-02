#!/usr/bin/env python3

__author__ = "Park Gunhui"

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
	if rc == 0: print("record_publisher connected success")
	else: print("Bad connection returned code: ", rc)

def record_publisher(record_command_queue):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("192.168.0.2", 1883, 60)

    while True:
        if not record_command_queue.empty():
            command = record_command_queue.get()
            client.publish("raspi/record", command)