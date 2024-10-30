#!/usr/bin/env python3

__author__ = ["Park Gunhui", "Hwang Hyeonjun"]

import time
from multiprocessing import Process, Queue, Array, Event

from transbot.bot_control import bot_control
from transbot.camera_capture import camera_capture
from transbot.line_tracing2 import line_tracing
from transbot.avoid_trees import lidar_scan
from transbot.avoid_trees import avoid_trees
from transbot.end_line_detect import end_line_detect
from transbot.obstacle_subscriber import obstacle_subscriber
from transbot.video_subscriber import video_subscriber
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
        lidar_array = Array('b', [False, False])

        camera_capture_event = Event()
        line_tracking_show_event = Event()
        lidar_scan_event = Event()
        end_line_detect_event = Event()
        end_line_show_event = Event()
        obstacle_event = Event()
        video_process_end_event = Event()

        camera_capture_process = Process(target=camera_capture, args=(frame_queue, camera_capture_event))
        line_tracing_process = Process(target=line_tracing, args=(frame_queue, control_queue, flag_queue, line_tracking_show_event))
        lidar_scan_process = Process(target=lidar_scan, args=(lidar_array, lidar_scan_event))
        avoid_trees_process = Process(target=avoid_trees, args=(lidar_array, control_queue))
        end_line_detect_process = Process(target=end_line_detect, args=(frame_queue, end_line_detect_event, end_line_show_event))
        obstacle_subscriber_process = Process(target=obstacle_subscriber, args=(obstacle_event,))
        video_subscriber_process = Process(target=video_subscriber, args=(video_process_end_event,))
        raspi_command_process = Process(target=raspi_command, args=(command_queue,))

        processes = [camera_capture_process, line_tracing_process, avoid_trees_process, end_line_detect_process, obstacle_subscriber_process, video_subscriber_process]

        ### CLI 환경 사용 시 비활성화 할 것 ###
        line_tracking_show_event.set()
        end_line_show_event.set()
        ### CLI 환경 사용 시 비활성화 할 것 ###

        camera_capture_process.start()
        time.sleep(CAMERA_CHECK_INTERVAL)
        print("camera_capture started.")

        ###  1. LINE_TRACING  ###

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
            time.sleep(1) # 정지선 인식 대기

        ###  2. AVOID_TREES  ###

        current_area = 0
        end_line_detected = False
        
        lidar_scan_process.start()
        avoid_trees_process.start()
        end_line_detect_process.start()
        raspi_command_process.start()
        obstacle_subscriber_process.start()
        video_subscriber_process.start()


        command_queue.put("start:obstacle_publisher_process")
        command_queue.put("start:video_publisher_process")
        command_queue.put(f"screen:{current_area + 1},z") # 1구간 분석 중 화면 표시
        area_start_time = time.time()

        while current_area < TOTAL_AREAS:
            command_queue.put("start:light")

            if obstacle_event.is_set():
                bot_control(0, 0)
                print("Obstacle detected.")
                while obstacle_event.is_set():
                    command_queue.put("end:light")
                    time.sleep(0.1)
                    command_queue.put("start:light")
                    time.sleep(0.1)
                area_start_time = time.time() - 1.5
                end_line_detect_event.clear()

            if not control_queue.empty():
                line, angular = control_queue.get()
                bot_control(line, angular)

            if (not end_line_detected) and (end_line_detect_event.is_set()) and ((time.time() - area_start_time) > 2):
                current_area += 1

                end_line_detected = True
                end_line_detect_time = time.time()

            # 정지선 탐지 후 몇초간 전진 후 정지
            if end_line_detected and ((time.time() - end_line_detect_time) > STOP_INTERVAL):
                bot_control(0,0)
                print(f"Area {current_area} finished.")
                end_line_detected = False
                command_queue.put("end:video_publisher_process") # 동영상 촬영 프로세스 종료
                while not video_process_end_event.is_set():
                    time.sleep(0.1)
                video_process_end_event.clear()
                if current_area < TOTAL_AREAS + 1: command_queue.put(f"screen:{current_area + 1},z") # 2~3구간 분석 중 화면 표시
                area_start_time = time.time()

                if current_area >= TOTAL_AREAS:
                    end_line_detect_process.terminate()
                    print("end_line_detect finished.")
                    avoid_trees_process.terminate()
                    print("avoid_trees finished.")
                    lidar_scan_event.set()
                    lidar_scan_process.join()
                    print("lidar_scan finished.")
                    camera_capture_event.set()
                    time.sleep(1)
                    camera_capture_process.terminate()
                    print("camera_capture finished.")
                    break

                command_queue.put("restart:video_publisher_process")
        
        ###  3. ARUCO_MARKER  ###

        command_queue.put("screen:0,0")

    finally:
        for process in processes:
            process.terminate()
        lidar_scan_event.set()
        lidar_scan_process.join(timeout=5)
        camera_capture_event.set()
        command_queue.put("end:light")
        time.sleep(1)
        bot_control(0, 0)

if __name__ == "__main__":
    main()