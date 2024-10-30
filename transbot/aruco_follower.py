#!/usr/bin/env python3

__author__ = "Bae Sunggyu"

import numpy as np
import cv2
import time

def aruco_follower(control_queue, finish_event):
   LINE_SPEED = 10
   ANGULAR_SPEED = 100

   # 카메라 캘리브레이션 파일 불러오기
   with np.load('/home/bot/arrc/camera_calibration.npz') as data:
       camera_matrix = data['camera_matrix']
       dist_coeffs = data['distortion_coefficients']
   
   # 7x7 타입의 딕셔너리만 사용
   aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_7X7_1000)
   parameters = cv2.aruco.DetectorParameters()
   
   MARKER_SIZE = 0.1  # 10cm
   TARGET_DISTANCE = 0.05  # 5cm
   DISTANCE_TOLERANCE = 0.005  # 허용 오차 ±0.5cm
   
   cap = cv2.VideoCapture(1)
   cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
   cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
   
   if not cap.isOpened():
       print("Error: Could not open camera.")
       return
   
   try:
       while True:
           ret, frame = cap.read()
           if not ret:
               continue
               
           gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
           corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
           
           if ids is not None:
               # 10번 마커 찾기
               marker_index = np.where(ids == 10)[0]
               if len(marker_index) > 0:
                   i = marker_index[0]
                   rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, MARKER_SIZE, camera_matrix, dist_coeffs)
                   
                   # 거리 계산
                   distance = np.sqrt(tvecs[i][0][0]**2 + tvecs[i][0][1]**2 + tvecs[i][0][2]**2)
                   # x, y 오프셋
                   x_offset = tvecs[i][0][0]
                   y_offset = tvecs[i][0][1]
                   
                   print(f"ID:10 Distance:{distance:.3f} X_offset:{x_offset:.3f} Y_offset:{y_offset:.3f}")
                   
                   # 목표 위치 도달 여부
                   if (abs(distance - TARGET_DISTANCE) < DISTANCE_TOLERANCE and 
                       abs(x_offset) < DISTANCE_TOLERANCE):
                       print("Position OK")
                       cap.release()
                       finish_event.set()
                       return  # 프로그램 종료
                       
                   # 로봇 제어
                   if abs(x_offset) > DISTANCE_TOLERANCE:
                       if x_offset > DISTANCE_TOLERANCE:
                           # 좌회전
                           control_queue.put((LINE_SPEED, -ANGULAR_SPEED))
                           time.sleep(0.025)
                       else:
                           # 우회전
                           control_queue.put((LINE_SPEED, ANGULAR_SPEED))
                           time.sleep(0.025)
                   else:
                       if distance > TARGET_DISTANCE + DISTANCE_TOLERANCE:
                           # 전진
                           control_queue.put((LINE_SPEED, 0))
                   
   except KeyboardInterrupt:
       cap.release()
       print("\nProgram terminated by user")