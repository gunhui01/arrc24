#!/usr/bin/env python3

__author__ = ["Park Gunhui", "Hwang Hyeonjun"]

import time
from multiprocessing import Process, Queue, Array, Event

from transbot.bot_control import bot_control
from transbot.camera_capture import camera_capture
from transbot.line_tracing import line_tracing
from transbot.avoid_trees import lidar_scan
from transbot.multi_lidar import avoid_trees
from transbot.multi_lidar import multi_lidar_scan
from transbot.multi_lidar import determine_direction
from transbot.end_line_detect import end_line_detect
from transbot.obstacle_subscriber import obstacle_subscriber
from transbot.raspi_command import raspi_command

QUEUE_CHECK_INTERVAL = 0.01
CAMERA_CHECK_INTERVAL = 1
STOP_INTERVAL = 0
TOTAL_AREAS = 3

def main():
    try:
        flag_queue = Queue()       # 다음 프로그램 진행 유무(Bool)
        control_queue = Queue()    # 모터의 속도, 각속도(Tuple)
        pause_queue = Queue()      # 모터 정지 유무(Bool)
        frame_queue = Queue()      # 카메라가 받은 이미지
        command_queue = Queue()    # 라즈베리 파이에 전달할 명령
        measure_array = Array('f', [0.0, 0.0])
        lidar_array = Array('b', [False, False])

        camera_capture_event = Event()
        lidar_scan_event = Event()
        end_line_detect_event = Event()
        obstacle_event = Event()

        camera_capture_process = Process(target=camera_capture, args=(frame_queue, camera_capture_event))
        line_tracing_process = Process(target=line_tracing, args=(frame_queue, control_queue, flag_queue))
        #lidar_scan_process = Process(target=lidar_scan, args=(lidar_array, lidar_scan_event))
        multi_lidar_scan_process = Process(target=multi_lidar_scan, args=(measure_array, lidar_scan_event))
        determine_direction_process = Process(target=determine_direction, args=(measure_array, lidar_array))
        avoid_trees_process = Process(target=avoid_trees, args=(lidar_array, control_queue))
        end_line_detect_process = Process(target=end_line_detect, args=(frame_queue, end_line_detect_event))
        obstacle_subscriber_process = Process(target=obstacle_subscriber, args=(obstacle_event,))
        raspi_command_process = Process(target=raspi_command, args=(command_queue,))

        processes = [camera_capture_process, line_tracing_process, multi_lidar_scan_process, determine_direction_process, avoid_trees_process, end_line_detect_process, obstacle_subscriber_process]

        camera_capture_process.start()
        time.sleep(CAMERA_CHECK_INTERVAL)
        print("camera_capture started.")

        ###  LINE_TRACING  ###

        line_tracing_process.start()
        print("line_tracing started.")
        line_tracing_start_time = time.time()
        while (time.time() - line_tracing_start_time) < CAMERA_CHECK_INTERVAL:
            if not control_queue.empty():
                line, angular = control_queue.get()

        while True:
            if not control_queue.empty():
                line, angular = control_queue.get()
                bot_control(line, angular)

            if not flag_queue.empty():
                finish = flag_queue.get()
                if finish:
                    line_tracing_process.terminate()
                    print("line_tracing finished.")
                    break
            time.sleep(QUEUE_CHECK_INTERVAL)

        ###  AVOID_TREES  ###

        current_area = 0
        end_line_detected = False

        multi_lidar_scan_process.start()
        determine_direction_process.start()
        print("lidar_scan started.")
        avoid_trees_process.start()
        print("avoid_trees started.")
        end_line_detect_process.start()
        print("end_line_detect started.")
        raspi_command_process.start()
        print("raspi_command started.")
        obstacle_subscriber_process.start()
        print("obstacle_subscriber started.")

        command_queue.put("screen:1,z")
        command_queue.put("obstacle_publisher_process")

        area_start_time = time.time()
        while current_area < TOTAL_AREAS:
            command_queue.put("light_on")

            if obstacle_event.is_set():
                bot_control(0, 0)
                print("Obstacle detected.")
                while obstacle_event.is_set():
                    command_queue.put("light_off")
                    time.sleep(0.1)
                    command_queue.put("light_on")
                    time.sleep(0.1)

            if not control_queue.empty():
                line, angular = control_queue.get()
                bot_control(line, angular)

            if (time.time() - area_start_time) > 1.5:
                end_line_detect_event.clear()

            if (not end_line_detected) and (end_line_detect_event.is_set()) and ((time.time() - area_start_time) > 2):
                current_area += 1
                print(f"Area {current_area} finished.")
                end_line_detected = True
                end_line_detect_time = time.time()

            if end_line_detected and ((time.time() - end_line_detect_time) > STOP_INTERVAL):
                end_line_detected = False
                bot_control(0,0)
                print("Bot Stopped")

                if current_area >= TOTAL_AREAS:
                    end_line_detect_process.terminate()
                    print("end_line_detect finished.")
                    avoid_trees_process.terminate()
                    print("avoid_trees finished.")
                    lidar_scan_event.set()
                    multi_lidar_scan_process.join()
                    print("lidar_scan finished.")
                    camera_capture_event.set()
                    time.sleep(1)
                    camera_capture_process.terminate()
                    print("camera_capture finished.")
                    break
                time.sleep(2) # 임시
                area_start_time = time.time()

        command_queue.put("screen:0,0")

    finally:
        for process in processes:
            process.terminate()
        lidar_scan_event.set()
        multi_lidar_scan_process.join()
        camera_capture_event.set()
        command_queue.put("light_off")
        time.sleep(1)
        bot_control(0, 0)

if __name__ == "__main__":
    main()