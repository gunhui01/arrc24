#!/usr/bin/env python3

__author__ = ["Heo Se Yeong", "Park Gunhui"]

from gpiozero import DistanceSensor, LED
import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc):
	if rc == 0: print("Connected success")
	else: print("Bad connection returned code: ", rc)

def on_publish(client, userdata, mid):
	print(f"Message published. MID: {mid}")

def obstacle_publisher():
    sensor_m = DistanceSensor(echo=26, trigger=20, max_distance=2.0)
    sensor_r = DistanceSensor(echo=23, trigger=22, max_distance=2.0)
    sensor_l = DistanceSensor(echo=27, trigger=17, max_distance=2.0)
    led = LED(21)
    led.on()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.connect("192.168.0.2", 1883, 60)

    client.loop_start()

    try:
        while True:
            client.publish("raspi/ultrasonic", str(sensor_m.distance * 100))
            client.publish("raspi/ultrasonic", str(sensor_r.distance * 100))
            client.publish("raspi/ultrasonic", str(sensor_l.distance * 100))
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        client.loop_stop()
        client.disconnect()