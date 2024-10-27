#!/usr/bin/env python3

__author__ = "Park Gunhui"

import paho.mqtt.client as mqtt

IP = "192.168.0.2"
TOPIC = "raspi/ultrasonic"

def on_connect(client, userdata, flags, rc):
	print("Connected with result code " + str(rc))
	client.subscribe(TOPIC)

def on_message(client, userdata, msg):
	print(msg.payload)

def obstacle_subscriber():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(IP, 1883, 60)
    client.loop_forever()