#!/usr/bin/env python3

__author__ = "Hwang Hyeonjun"

import paho.mqtt.client as mqtt
import cv2
import threading
import time
import base64

def mqtt_video_publisher(index, output_files):
    chunk_size = 256 * 1024  # 256KB로 청크 설정
    client = mqtt.Client()
    client.connect("192.168.0.2", 1883, 60)
    client.loop_start()

    try:
        # 파일을 청크 단위로 분할하여 전송
        for idx, path in zip(index, output_files):
            with open(path, "rb") as file:
                chunk_number = 0
                while chunk := file.read(chunk_size):
                    encoded_chunk = base64.b64encode(chunk).decode("utf-8")
                    client.publish(f"raspi/video{idx}", encoded_chunk)
                    chunk_number += 1

    finally:
        client.loop_stop()
        client.disconnect()


### 실행 함수 ###
camera_indices = [1, 2]
output_files = [f'output_video_{i}.mp4' for i in camera_indices]

def video_publisher(frame_queue, video_publisher_event):
    
    # Use MJPG codec to increase compatibility
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    while True:
        out1 = cv2.VideoWriter("output_video_1.mp4", fourcc, 60, (1280, 720))
        out2 = cv2.VideoWriter("output_video_2.mp4", fourcc, 60, (1280, 720))
        idx_temp = None
        print("1")
        while True:
            try:
                idx, frame = frame_queue.get()

                if idx_temp is None:
                    idx_temp = idx

                if idx == idx_temp:
                    out1.write(frame)
                else:
                    out2.write(frame)

            except Empty:
                print("Frame queue is empty, waiting for frames...")
                continue
                
            # 종료 명령 전달 시
            if video_publisher_event.is_set():
                print("Saving video files...")
                out1.release()
                out2.release()
                print("Saving complete.")
                print("MQTT video sending...")
                mqtt_video_publisher(camera_indices, output_files)
                print("MQTT video sending complete.")

                # 다시 이벤트가 False로 바뀔 때까지 대기
                while video_publisher_event.is_set():
                    time.sleep(0.1)
            continue
