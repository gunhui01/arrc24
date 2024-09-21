#!/usr/bin/env python3

import time
from multiprocessing import Process, Queue

from transbot.bot_control import bot_control
from transbot.camera_capture import camera_capture
from transbot.line_tracing import line_tracing
from transbot.avoid_trees import lidar_scan
from transbot.avoid_trees import avoid_trees

QUEUE_CHECK_INTERVAL = 0.01
WAIT_INTERVAL = 1

def main():
    try:
        flag_queue = Queue()    # 다음 프로그램 진행 유무(Bool)
        control_queue = Queue() # 모터의 속도, 각속도(Tuple)
        pause_queue = Queue()   # 모터 정지 유무(Bool)
        frame_queue = Queue()   # 카메라가 받은 이미지
        lidar_queue = Queue()   # LiDAR가 받은 데이터

        camera_capture_process = Process(target=camera_capture, args=(frame_queue,))
        line_tracing_process = Process(target=line_tracing, args=(frame_queue, control_queue, flag_queue))
        lidar_scan_process = Process(target=lidar_scan, args=(lidar_queue,))
        avoid_trees_process = Process(target=avoid_trees, args=(lidar_queue, control_queue))

        camera_capture_process.start()
        time.sleep(WAIT_INTERVAL)
        print("camera_capture started.")

        ###  LINE_TRACING  ###

        line_tracing_process.start()
        print("line_tracing started.")

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

        lidar_scan_process.start()
        time.sleep(WAIT_INTERVAL)
        print("lidar_scan started.")

        avoid_trees_process.start()
        print("avoid_trees started.")

        while True:
            if not control_queue.empty():
                line, angular = control_queue.get()
                bot_control(line, angular)
            time.sleep(QUEUE_CHECK_INTERVAL)

    finally:
        camera_capture_process.terminate()
        line_tracing_process.terminate()
        lidar_scan_process.terminate()
        avoid_trees_process.terminate()
        bot_control(0, 0)

if __name__ == "__main__":
    main()