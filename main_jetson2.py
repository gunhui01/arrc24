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
from transbot.raspi_command import raspi_command
from transbot.aruco_follower import aruco_follower

QUEUE_CHECK_INTERVAL = 0.01
CAMERA_CHECK_INTERVAL = 1
STOP_INTERVAL = 0
TOTAL_AREAS = 3

def main():
    try:
        control_queue = Queue()    # 모터의 속도, 각속도(Tuple)
        frame_queue = Queue()      # 카메라가 받은 이미지
        command_queue = Queue()    # 라즈베리 파이에 전달할 명령
        lidar_array = Array('b', [False, False])

        camera_capture_event = Event()
        line_tracking_end_event = Event()
        line_tracking_show_event = Event()
        lidar_scan_event = Event()
        end_line_detect_event = Event()
        end_line_show_event = Event()
        obstacle_event = Event()
        finish_event = Event()

        camera_capture_process = Process(target=camera_capture, args=(frame_queue, camera_capture_event))
        line_tracing_process = Process(target=line_tracing, args=(frame_queue, control_queue, line_tracking_end_event, line_tracking_show_event))
        lidar_scan_process = Process(target=lidar_scan, args=(lidar_array, lidar_scan_event))
        avoid_trees_process = Process(target=avoid_trees, args=(lidar_array, control_queue))
        end_line_detect_process = Process(target=end_line_detect, args=(frame_queue, end_line_detect_event, end_line_show_event))
        obstacle_subscriber_process = Process(target=obstacle_subscriber, args=(obstacle_event,))
        raspi_command_process = Process(target=raspi_command, args=(command_queue,))
        aruco_follower_process = Process(target=aruco_follower, args=(control_queue, finish_event))

        processes = [camera_capture_process, line_tracing_process, avoid_trees_process, end_line_detect_process, obstacle_subscriber_process]

        ### CLI 환경 사용 시 비활성화 할 것 ###
        line_tracking_show_event.set()
        end_line_show_event.set()
        ### CLI 환경 사용 시 비활성화 할 것 ###

        ###  1. LINE_TRACING  ###

        print("Line tracking started.")
        camera_capture_process.start()
        line_tracing_process.start()

        # line_tracing_start_time = time.time()
        # while (time.time() - line_tracing_start_time) < CAMERA_CHECK_INTERVAL:
        #     if not control_queue.empty():
        #         line, angular = control_queue.get()

        while True:
            if not control_queue.empty():
                # 최신 프레임을 유지하기 위해 큐를 계속 비움
                while control_queue.qsize() > 1:
                    control_queue.get()  # 오래된 프레임 버리기
                line, angular = control_queue.get()
                bot_control(line, angular)

            if line_tracking_end_event.is_set():
                time.sleep(1) # 정지선 검출 1초 후 정지
                bot_control(0,0)
                line_tracing_process.terminate()
                print("line_tracing finished.")
                break

        ###  2. AVOID_TREES  ###

        current_area = 1
        
        lidar_scan_process.start()
        avoid_trees_process.start()
        end_line_detect_process.start()
        raspi_command_process.start()
        obstacle_subscriber_process.start()

        command_queue.put("start:obstacle_publisher_process")
        command_queue.put("screen:x")
        area_start_time = time.time()
        obstacle = False

        command_queue.put("start:light") # 라이트 켜기

        # 구역별 반복문
        while True:
            # 장애물이 감지될 경우
            if obstacle_event.is_set():
                bot_control(0, 0) # 봇 정지
                print("Obstacle detected.")
                obstacle = True # 장애물 구간 플래그 활성화
                command_queue.put("screen:y")
                while obstacle_event.is_set(): # 장애물이 제거될 때 까지 대기
                    command_queue.put("end:light")
                    time.sleep(0.1)
                    command_queue.put("start:light")
                    time.sleep(0.1)
                time.sleep(1) # 장애물이 치워진 후 1초 대기
                current_area += 1
                if current_area > TOTAL_AREAS:
                    break
                if not control_queue.empty():
                    # 최신 프레임을 유지하기 위해 큐를 계속 비움
                    while control_queue.qsize() > 1:
                        control_queue.get()  # 오래된 프레임 버리기
                end_line_detect_event.clear()

            if not control_queue.empty():
                # 최신 프레임을 유지하기 위해 큐를 계속 비움
                while control_queue.qsize() > 1:
                    control_queue.get()  # 오래된 프레임 버리기
                line, angular = control_queue.get()
                bot_control(line, angular)

            # area 출발한 지 1초 전까지는 end_line을 detect하지 못하도록 함
            if (time.time() - area_start_time) < 1:
                end_line_detect_event.clear()

            if end_line_detect_event.is_set():
                bot_control(0,0) # 정지
                print(f"Area {current_area} finished.")
                current_area += 1
                if not obstacle: # 장애물 구간이 아닌 경우
                    command_queue.put("screen:7")
                
                if current_area <= TOTAL_AREAS: # 전구간이 아직 끝나지 않은 경우
                    command_queue.put(f"screen:x")
                    area_start_time = time.time()
                else: # 모든 구간이 끝난 경우
                    break

        obstacle = False

        # 구간 종료 코드
        end_line_detect_process.terminate()
        avoid_trees_process.terminate()
        lidar_scan_event.set()
        lidar_scan_process.join(timeout=5)
        camera_capture_event.set()
        time.sleep(1)
        camera_capture_process.terminate()
        
        ###  3. ARUCO_FOLLOWER  ###

        command_queue.put("screen:z")
        aruco_follower_process.start()

        while not finish_event.is_set():
            if not control_queue.empty():
                line, angular = control_queue.get()
                bot_control(line, angular)

    finally:
        bot_control(0, 0)
        print("Bot stopped.")
        for process in processes:
            process.terminate()
            print(f"{process} terminated.")
        lidar_scan_event.set()
        lidar_scan_process.join(timeout=5)
        print("lidar_scan_process terminated.")
        camera_capture_event.set()
        print("camera_capture_event terminated.")
        command_queue.put("end:light")

if __name__ == "__main__":
    main()