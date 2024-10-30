#!/usr/bin/env python3

__author__ = "Bae Sunggyu"

import numpy as np
import cv2
import time
import sys

def aruco_follower(control_queue, finish_event):
   LINE_SPEED = 10
   ANGULAR_SPEED = 100
   # 카메라 캘리브레이션 파일 불러오기
   with np.load('/home/bot/arrc24/camera_calibration.npz') as data:
       camera_matrix = data['camera_matrix']
       dist_coeffs = data['distortion_coefficients']
   
   # 7x7 타입의 딕셔너리만 사용
   aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_7X7_1000)
   aruco_detector = cv2.aruco.ArucoDetector(aruco_dict)
   
   MARKER_SIZE = 0.1  # 10cm
   CENTER_TOLERANCE = 0.02  # 중심 정렬 허용 오차
   
   cap = cv2.VideoCapture(1)
   cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
   cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
   
   if not cap.isOpened():
       print("Error: Could not open camera.")
       return

   marker_lost_time = None  # 마커를 잃어버린 시간
   marker_found_once = False  # 마커를 한번이라도 발견했는지
   last_distance = None  # 마지막으로 측정된 거리
   
   try:
       while True:
           ret, frame = cap.read()
           if not ret:
               continue
               
           gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
           corners, ids, _ = aruco_detector.detectMarkers(gray)
           
           if ids is not None:
               marker_index = np.where(ids == 10)[0]
               if len(marker_index) > 0:
                   i = marker_index[0]
                   objPoints = np.array([[-MARKER_SIZE/2, MARKER_SIZE/2, 0],
                                       [MARKER_SIZE/2, MARKER_SIZE/2, 0],
                                       [MARKER_SIZE/2, -MARKER_SIZE/2, 0],
                                       [-MARKER_SIZE/2, -MARKER_SIZE/2, 0]], dtype=np.float32)
                   success, rvec, tvec = cv2.solvePnP(objPoints, corners[i], camera_matrix, dist_coeffs)
                   
                   # 거리와 오프셋 계산
                   distance = float(np.sqrt(tvec[0]**2 + tvec[1]**2 + tvec[2]**2))
                   x_offset = float(tvec[0])
                   last_distance = distance  # 현재 거리 저장
                   
                   print(f"Distance: {distance:.3f}m, X_offset: {x_offset:.3f}m")
                   
                   marker_found_once = True
                   marker_lost_time = None
                   
                   # 중심 정렬 및 이동 로직
                   if abs(x_offset) > CENTER_TOLERANCE:
                       # 회전 방향 결정
                       if x_offset > 0:
                           control_queue.put((0, ANGULAR_SPEED/4))  # 우회전
                       else:
                           control_queue.put((0, -ANGULAR_SPEED/4))  # 좌회전
                   else:
                       # 중심이 맞춰져 있으면 직진
                       control_queue.put((LINE_SPEED, 0))
           else:
               if marker_found_once:  # 마커를 한번이라도 봤었다면
                   if marker_lost_time is None:
                       marker_lost_time = time.time()
                       print(f"Marker lost at distance {last_distance:.3f}m, moving forward for 1 second...")
                       control_queue.put((LINE_SPEED, 0))  # 직진
                   elif time.time() - marker_lost_time >= 2:  # 1초가 지났으면
                       print(f"Stopping after 1 second forward movement. Last known distance: {last_distance:.3f}m")
                       control_queue.put((0, 0))  # 정지
                       cap.release()
                       finish_event.set()
                       sys.exit(0)
               else:
                   # 마커를 한번도 못 봤으면 계속 회전하며 탐색
                   control_queue.put((0, ANGULAR_SPEED/4))
                   
   except KeyboardInterrupt:
       cap.release()
       print("\nProgram terminated by user")
       sys.exit(0)

   finally:
       cap.release()
       cv2.destroyAllWindows()
       sys.exit(0)