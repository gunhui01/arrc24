#!/usr/bin/env python3

import time
from multiprocessing import Process, Queue

from transbot.bot_control import bot_control
from transbot.camera_capture import camera_capture
from transbot.line_tracing import line_tracing
from transbot.avoid_trees import avoid_trees

QUEUE_CHECK_INTERVAL = 0.01

def main():
    flag_queue = Queue()    # 다음 프로그램 진행 유무(Bool)
    control_queue = Queue() # 모터의 속도, 각속도(Tuple)
    pause_queue = Queue()   # 모터 정지 유무(Bool)
    frame_queue = Queue()   # 카메라가 받은 이미지

    camera_capture_process = Process(target=line_tracing, args=(frame_queue,))
    line_tracing_process = Process(target=line_tracing, args=(frame_queue, control_queue, flag_queue))
    avoid_trees_process = Process(target=avoid_trees, args=(control_queue,))

    camera_capture_process.start()
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

if __name__ == "__main__":
    main()