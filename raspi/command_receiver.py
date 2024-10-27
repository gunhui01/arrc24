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
    print("Userdata on connect:", userdata)

def on_message(client, userdata, msg):
    if msg.payload.decode("utf-8") == "obstacle_publisher_process":
        if userdata.get("obstacle_publisher_process") and not userdata["obstacle_publisher_process"].is_alive():
            userdata["obstacle_publisher_process"].start()
    elif msg.payload.decode("utf-8") == "light_on":
        userdata.get("light_on", lambda: None)()
    elif msg.payload.decode("utf-8") == "light_off":
        userdata.get("light_off", lambda: None)()

def command_receiver():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    userdata = {
        "obstacle_publisher_process": Process(target=obstacle_publisher),
        "light_on": light_control.on,
        "light_off": light_control.off
    }

    client.user_data_set(userdata)
    client.connect("192.168.0.2", 1883, 60)
    client.loop_forever()