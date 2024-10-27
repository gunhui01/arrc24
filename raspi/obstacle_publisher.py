#!/usr/bin/env python3

__author__ = ["Heo Se Yeong", "Park Gunhui"]

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc):
	if rc == 0: print("Connected success")
	else: print("Bad connection returned code: ", rc)

def on_publish(client, userdata, mid):
	print(f"Message published. MID: {mid}")

def measure_distance(trig_pin, echo_pin):
    GPIO.output(trig_pin, False)
    time.sleep(0.1)

    GPIO.output(trig_pin, True)
    time.sleep(0.00001)
    GPIO.output(trig_pin, False)

    while GPIO.input(echo_pin) == 0:
        pulse_start = time.time()

    while GPIO.input(echo_pin) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    return round(distance, 2)

def obstacle_publisher():
    TRIG_PIN_L = 17
    ECHO_PIN_L = 27
    TRIG_PIN_R = 22
    ECHO_PIN_R = 23
    TRIG_PIN_M = 20
    ECHO_PIN_M = 26

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG_PIN_L, GPIO.OUT)
    GPIO.setup(ECHO_PIN_L, GPIO.IN)
    GPIO.setup(TRIG_PIN_R, GPIO.OUT)
    GPIO.setup(ECHO_PIN_R, GPIO.IN)
    GPIO.setup(TRIG_PIN_M, GPIO.OUT)
    GPIO.setup(ECHO_PIN_M, GPIO.IN)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.connect("192.168.0.2", 1883, 60)

    client.loop_start()

    try:
        while True:
            client.publish("raspi/ultrasonic", str(measure_distance(TRIG_PIN_M, ECHO_PIN_M)))
            client.publish("raspi/ultrasonic", str(measure_distance(TRIG_PIN_R, ECHO_PIN_R)))
            client.publish("raspi/ultrasonic", str(measure_distance(TRIG_PIN_L, ECHO_PIN_L)))
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    obstacle_publisher()