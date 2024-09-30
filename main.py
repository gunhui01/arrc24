#!/usr/bin/env python3

__author__ = "Park Gunhui"
__credits__ = ["Hwang Hyeonjun"]

import time
from multiprocessing import Process, Queue, Array

from transbot.bot_control import bot_control
from transbot.camera_capture import camera_capture
from transbot.line_tracing import line_tracing
from transbot.avoid_trees import lidar_scan
from transbot.avoid_trees import avoid_trees
from transbot.end_line_detect import end_line_detect

QUEUE_CHECK_INTERVAL = 0.01
CAMERA_CHECK_INTERVAL = 1
STOP_INTERVAL = 2

def main():
    try:
        flag_queue = Queue()    # 다음 프로그램 진행 유무(Bool)
        control_queue = Queue() # 모터의 속도, 각속도(Tuple)
        pause_queue = Queue()   # 모터 정지 유무(Bool)
        frame_queue = Queue()   # 카메라가 받은 이미지
        lidar_array = Array('b', [False, False])

        camera_capture_process = Process(target=camera_capture, args=(frame_queue,))
        line_tracing_process = Process(target=line_tracing, args=(frame_queue, control_queue, flag_queue))
        lidar_scan_process = Process(target=lidar_scan, args=(lidar_array,))
        avoid_trees_process = Process(target=avoid_trees, args=(lidar_array, control_queue))
        end_line_detect_process = Process(target=end_line_detect, args=(frame_queue, flag_queue))

        camera_capture_process.start()
        time.sleep(CAMERA_CHECK_INTERVAL)
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
        print("lidar_scan started.")
        avoid_trees_process.start()
        print("avoid_trees started.")
        end_line_detect_process.start()
        print("end_line_detect started.")

        while True:
            if not control_queue.empty():
                line, angular = control_queue.get()
                bot_control(line, angular)

            if not flag_queue.empty():
                finish = flag_queue.get()
                if finish:
                    end_line_detect_process.terminate()
                    print("end_line_detect finished.")
                    end_line_detect_time = time.time()
                    break

        while (time.time() - end_line_detect_time) < STOP_INTERVAL:
            if not control_queue.empty():
                line, angular = control_queue.get()
                bot_control(line, angular)

        avoid_trees_process.terminate()
        print("avoid_trees finished.")
        lidar_scan_process.terminate()
        print("lidar_scan finished.")
    finally:
        camera_capture_process.terminate()
        line_tracing_process.terminate()
        lidar_scan_process.terminate()
        avoid_trees_process.terminate()
        end_line_detect_process.terminate()
        bot_control(0, 0)

if __name__ == "__main__":
    main()