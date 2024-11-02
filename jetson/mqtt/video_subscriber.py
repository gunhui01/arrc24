#!/usr/bin/env python3

__author__ = "Hwang Hyeonjun"

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("raspi/video_process_status")

def on_message(client, userdata, msg):
    message = str(msg.payload.decode("utf-8"))

    if message == "video_publisher_process ended":
        userdata["video_process_end_event"].set()
    else:
        userdata["video_process_end_event"].clear()

def video_subscriber(video_process_end_event):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.user_data_set({"video_process_end_event":video_process_end_event})

    client.connect("192.168.0.2", 1883, 60)
    client.loop_forever()