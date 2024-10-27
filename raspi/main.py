#!/usr/bin/env python3

__author__ = "Park Gunhui"

import time
from multiprocessing import Process, Queue, Array, Event
import paho.mqtt.client as mqtt

import light_control
from obstacle_publisher import obstacle_publisher

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("jetson/command")

def on_message(client, userdata, msg):
    print(msg.payload)
    if msg.payload.decode("utf-8") == "obstacle_publisher_process":
        userdata["obstacle_publisher_process"].start()
    elif msg.payload.decode("utf-8") == "light_on":
        userdata["light_on"]
    elif msg.payload.decode("utf-8") == "light_off":
        userdata["light_off"]

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    obstacle_publisher_process = Process(target=obstacle_publisher)

    client.user_data_set({"obstacle_publisher_process":obstacle_publisher_process})
    client.user_data_set({"light_on":light_control.on()})
    client.user_data_set({"light_off":light_control.off()})

    client.connect("192.168.0.2", 1883, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()