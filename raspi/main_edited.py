#!/usr/bin/env python3

__author__ = ["Park Gunhui", "Hwang Hyeonjun"]

import time
from multiprocessing import Process, Queue, Array, Event
import paho.mqtt.client as mqtt

import light_control
from obstacle_publisher import obstacle_publisher
from video_publisher import video_publisher
from camera_capture import camera_capture

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("jetson/command")
    print("Userdata on connect:", userdata)

def on_message(client, userdata, msg):
    # obstacle_publisher_process (start)
    if msg.payload.decode("utf-8") == "start:obstacle_publisher_process":
        if userdata.get("obstacle_publisher_process") and not userdata["obstacle_publisher_process"].is_alive():
            userdata["obstacle_publisher_process"].start()
    elif msg.payload.decode("utf-8") == "light_on":
        userdata.get("light_on", lambda: None)()
    elif msg.payload.decode("utf-8") == "light_off":
        userdata.get("light_off", lambda: None)()

    # video_publisher_process (start)
    elif msg.payload.decode("utf-8") == "start:video_publisher_process":
        if userdata.get("video_publisher_process") and not userdata["video_publisher_process"].is_alive():
            userdata["video_publisher_process"].start()

    # video_publisher_process (restart)
    elif msg.payload.decode("utf-8") == "restart:video_publisher_process":
        userdata["video_publisher_event"].clear()

    # video_publisher_process (area finished)
    elif msg.payload.decode("utf-8") == "end:video_publisher_process":
        print("구간 종료 신호 감지됨")
        userdata["video_publisher_event"].set()
        time.sleep(5) #임시
        # 종료 신호 publish
        client.publish("raspi/video_process_status", "video_publisher_process ended")

def main():
    ### MQTT Client Connect ###
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    frame_queue = Queue()
    video_publisher_event = Event()
    camera_capture_event = Event()

    userdata = {
        "obstacle_publisher_process": Process(target=obstacle_publisher),
        "light_on": light_control.on,
        "light_off": light_control.off,
        "video_publisher_process": Process(target=video_publisher, args=(frame_queue, video_publisher_event)),
        "video_publisher_event": video_publisher_event
    }

    client.user_data_set(userdata)
    client.connect("192.168.0.2", 1883, 60)
    client.loop_start()

    ### Camera Capture Start ###
    camera_capture_process = Process(target=camera_capture, args=(frame_queue, camera_capture_event))
    camera_capture_process.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # 프로세스 종료 및 정리
        video_publisher_event.set()
        camera_capture_event.set()

        if userdata["obstacle_publisher_process"].is_alive():
            userdata["obstacle_publisher_process"].join()
        if userdata["video_publisher_process"].is_alive():
            userdata["video_publisher_process"].join()
        if camera_capture_process.is_alive():
            camera_capture_process.join()
        client.loop_stop()

if __name__ == "__main__":
    main()