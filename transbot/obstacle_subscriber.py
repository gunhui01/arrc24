#!/usr/bin/env python3

__author__ = "Park Gunhui"

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("raspi/ultrasonic")

def on_message(client, userdata, msg):
    detected = bool(msg.payload.decode("utf-8"))

    if detected:
        userdata["obstacle_event"].set()
    else:
        userdata["obstacle_event"].clear()

def obstacle_subscriber(obstacle_event):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.user_data_set({"obstacle_event":obstacle_event})

    client.connect("192.168.0.2", 1883, 60)
    client.loop_forever()