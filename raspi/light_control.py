#!/usr/bin/env python3

__author__ = ["Heo Se Yeong", "Park Gunhui"]

import RPi.GPIO as GPIO
import time

LED_PIN = 21
GPIO.setup(LED_PIN, GPIO.OUT)

def on():
    GPIO.output(LED_PIN, GPIO.HIGH)

def off():
    GPIO.output(LED_PIN, GPIO.LOW)