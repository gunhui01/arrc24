#!/usr/bin/env python3

__author__ = "Hwang Hyeonjun"

import paho.mqtt.client as mqtt
import cv2
import time
import queue

def video_recorder(frame_queue, video_record_event, video_saving_event):
    
    # Set File Codec
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    while True:
        if video_record_event.is_set():
            outs = [cv2.VideoWriter(f"{i}.mp4", fourcc, 60, (1280, 720)) for i in range (1,3)]
            print("Side Camera Recording Started.")
            idx_temp = None
            try:
                while not video_saving_event.is_set():
                    try:
                        idx, frame = frame_queue.get(timeout=1)
                        if not idx_temp:
                            idx_temp = idx
                        
                        if idx == idx_temp:
                            outs[0].write(frame)
                        else:
                            outs[1].write(frame)

                    except queue.Empty:
                        continue
                    except Exception as e:
                        print("An error occured: ", e)
            finally:
                # 종료 명령 전달 시
                print("Saving video files...")
                for out in outs:
                    out.release()
                print("Saving complete.")
                video_record_event.clear()

        # video_record_event를 확인하는 간격 설정
        time.sleep(0.1)
