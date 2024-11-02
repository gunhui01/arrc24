#!/usr/bin/env python3

__author__ = "Hwang Hyeonjun"

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("raspi/counted")

def on_message(client, userdata, msg):
    message = str(msg.payload.decode("utf-8"))

    if message == "1":
        userdata["apple_counted_event"].set()
    else:
        userdata["apple_counted_event"].clear()

def apple_subscriber(apple_counted_event):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.user_data_set({"apple_counted_event":apple_counted_event})

    client.connect("192.168.0.2", 1883, 60)
    client.loop_forever()