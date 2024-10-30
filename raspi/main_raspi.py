#!/usr/bin/env python3

__author__ = ["Park Gunhui", "Hwang Hyeonjun"]

import paho.mqtt.client as mqtt
from multiprocessing import Process, Queue, Event
import time

from screen_display import screen_display
from camera_capture import camera_capture
from video_recorder import video_recorder
from obstacle_publisher import obstacle_publisher
from apple_count_subscriber import apple_count_subscriber
import light_control

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("jetson/command")
    print("Userdata on connect:", userdata)

def on_message(client, userdata, msg):
    if msg.payload:
        message = msg.payload.decode("utf-8")
        cmd, ps = message.split(':')

        ## start: ##
        if cmd == "start":
            if ps == "light":
                userdata.get("light_on", lambda: None)()
            elif ps == "obstacle_publisher_process":
                obstacle_publisher_process = userdata.get("obstacle_publisher_process")
                if not obstacle_publisher_process.is_alive():
                    obstacle_publisher_process.start()
            elif ps == "video_recorder_process":
                video_recorder_process = userdata.get("video_recorder_process")
                if not video_recorder_process.is_alive():
                    video_recorder_process.start()
            elif ps == "apple_count_subscriber_process":
                userdata.get("apple_count_subscriber_process").start()
        ## restart: ##
        elif cmd == "restart":
            if ps == "video_recorder_process":
                userdata.get("video_recorder_event").clear()
        ## end: ##
        elif cmd == "end":
            if ps == "light":
                userdata.get("light_off", lambda: None)()
            elif ps == "video_recorder_process":
                print("Area termination signal detected.")
                video_recorder_event = userdata.get("video_recorder_event")
                video_recorder_event.set() # Save recorded video file
                time.sleep(1)
                while not video_recorder_event.is_set(): # Wait for the event to clear
                    time.sleep(1)
                # Publish end signal to Jetson
                client.publish("raspi/video_process_status", "video_recorder_process ended")
        ## screen: ##
        elif cmd == "screen":
            userdata.get("command_share_queue").put(message)

def main():
    try:
        ## Define Queue, Event, Process ##
        display_info_queue = Queue()
        command_share_queue = Queue()
        frame_queue = Queue()
        apple_count_queue = Queue()

        camera_capture_event = Event()
        video_recorder_event = Event()

        screen_display_process = Process(target=screen_display, args=(command_share_queue, apple_count_queue))
        camera_capture_process = Process(target=camera_capture, args=(frame_queue, camera_capture_event))
        obstacle_publisher_process = Process(target=obstacle_publisher)
        video_recorder_process = Process(target=video_recorder, args=(frame_queue, video_recorder_event))
        apple_count_subscriber_process = Process(target=apple_count_subscriber, args=(apple_count_queue,))

        always_running_processes = [screen_display_process, camera_capture_process]
        events = [camera_capture_event, video_recorder_event]

        ## MQTT Client Settings ##
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        userdata = {
            "obstacle_publisher_process": obstacle_publisher_process,
            "light_on": light_control.on,
            "light_off": light_control.off,
            "video_recorder_process": video_recorder_process,
            "video_recorder_event": video_recorder_event,
            "command_share_queue": command_share_queue,
            "apple_count_subscriber_process": apple_count_subscriber_process
        }
        client.user_data_set(userdata)
        client.connect("192.168.0.2", 1883, 60)
        client.loop_start()

        for process in always_running_processes:
            process.start()

        ## Loop ##
        while True:
            time.sleep(1)

    finally:
        client.loop_stop()
        for event in events:
            event.set()
        for process in always_running_processes:
            if process.is_alive():
                process.join()

if __name__ == "__main__":
    main()