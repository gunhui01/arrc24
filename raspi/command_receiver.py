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
    message = msg.payload.decode("utf-8")

    if message[:7] == "screen:":
        userdata["command_share_queue"].put(message)

    if message == "obstacle_publisher_process":
        if userdata.get("obstacle_publisher_process") and not userdata["obstacle_publisher_process"].is_alive():
            userdata["obstacle_publisher_process"].start()
    elif message == "light_on":
        userdata.get("light_on", lambda: None)()
    elif message == "light_off":
        userdata.get("light_off", lambda: None)()

def command_receiver(command_share_queue):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    userdata = {
        "command_share_queue": command_share_queue,
        "obstacle_publisher_process": Process(target=obstacle_publisher),
        "light_on": light_control.on,
        "light_off": light_control.off
    }

    client.user_data_set(userdata)
    client.connect("192.168.0.2", 1883, 60)
    client.loop_forever()