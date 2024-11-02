#!/usr/bin/env python3

__author__ = ["Park Gunhui", "Hwang Hyeonjun"]

from multiprocessing import Process, Queue, Event
import raspi as rp
import time

def main():
    try:
        ## Define Queue, Event, Process ##
        display_info_queue = Queue()
        command_share_queue = Queue()
        frame_queue = Queue()
        apple_count_queue = Queue()
        record_command_queue = Queue()

        camera_capture_event = Event()
        video_recorder_event = Event()

        mqtt_handler_process = Process(target=rp.mqtt_handler.run_mqtt_client, args=(userdata,))
        screen_display_process = Process(target=rp.screen_display, args=(command_share_queue, apple_count_queue))
        camera_capture_process = Process(target=rp.camera_capture, args=(frame_queue, camera_capture_event))
        obstacle_publisher_process = Process(target=rp.obstacle_publisher)
        video_recorder_process = Process(target=rp.video_recorder, args=(frame_queue, video_recorder_event))
        apple_count_subscriber_process = Process(target=rp.apple_count_subscriber, args=(apple_count_queue,))
        record_publisher_process = Process(target=rp.record_publisher, args=(record_command_queue,))

        always_running_processes = [mqtt_handler_process, screen_display_process, camera_capture_process]
        events = [camera_capture_event, video_recorder_event]

        ## MQTT Client Process ##
        userdata = {
            "obstacle_publisher_process": obstacle_publisher_process,
            "light_on": rp.light_control.on,
            "light_off": rp.light_control.off,
            "video_recorder_process": video_recorder_process,
            "video_recorder_event": video_recorder_event,
            "command_share_queue": command_share_queue,
            "apple_count_subscriber_process": apple_count_subscriber_process
        }
        
        # 항상 실행해야 하는 프로세스들 시작
        for process in always_running_processes:
            process.start()

        ## Loop ##
        while True:
            time.sleep(1)

    finally:
        for event in events:
            event.set()
        for process in always_running_processes:
            if process.is_alive():
                process.join()

if __name__ == "__main__":
    main()