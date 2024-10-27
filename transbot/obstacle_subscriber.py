#!/usr/bin/env python3

__author__ = "Park Gunhui"

import paho.mqtt.client as mqtt

DETECT_RANGE = 10 #cm

def on_connect(client, userdata, flags, rc):
	print("Connected with result code " + str(rc))
	client.subscribe("raspi/ultrasonic")

def on_message(client, userdata, msg):
	print(msg.payload)
	if float(msg.payload.decode("utf-8")) <= DETECT_RANGE:
		userdata["obstacle_queue"].put(True)
		print("True")

def obstacle_subscriber(obstacle_queue):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.user_data_set({"obstacle_queue":obstacle_queue})

    client.connect("192.168.0.2", 1883, 60)
    client.loop_forever()