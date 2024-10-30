#!/usr/bin/env python3

__author__ = "Park Gunhui"

import paho.mqtt.client as mqtt
import os, time

def on_connect(client, userdata, flags, rc):
	if rc == 0: print("Connected success")
	else: print("Bad connection returned code: ", rc)

def apple_count_subscriber(apple_count_queue):
    MONITORING_DIR = "/home/bot/Desktop/shared"
    # MONITORING_DIR = "./"
    counted_area = 1

    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect("192.168.0.2", 1883, 60)

    while counted_area < 2:
        txt_files = [f for f in os.listdir(MONITORING_DIR) if f.endswith(".txt") and f.startswith(f'{counted_area}')]
        if txt_files:
            _, tmp = txt_files[0].split('_')
            count, _ = tmp.split('.')
            apple_count_queue.put(count)
            counted_area += 1
            client.publish("raspi/counted", "1")
        time.sleep(1)