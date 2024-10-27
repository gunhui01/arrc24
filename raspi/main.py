#!/usr/bin/env python3

__author__ = "Park Gunhui"

import time
from multiprocessing import Process, Queue, Array, Event
import paho.mqtt.client as mqtt

import obstacle_publisher

def on_connect(client, userdata, flags, rc):
	print("Connected with result code " + str(rc))
	client.subscribe("jetson/command")

def on_message(client, userdata, msg):
	print(msg.payload)
	if msg.payload.decode("utf-8") == "obstacle":
		userdata["obstacle_publish_process"].start()

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    obstacle_publish_process = Process(target=obstacle_publisher)

    client.user_data_set({"obstacle_publish_process":obstacle_publish_process})

    client.connect("192.168.0.2", 1883, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()