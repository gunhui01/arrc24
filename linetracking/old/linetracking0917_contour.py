from Transbot_Lib import Transbot
from ipywidgets import interact
import ipywidgets as widgets
import time
import math
import cv2
import numpy as np

bot = Transbot()

# 데이터 수신 설정
bot.create_receive_threading()
bot.set_auto_report_state(True, forever=False)

# 조명 설정
bot.set_colorful_effect(5, speed=255, parm=255)

# bot.get_imu_state()

# PID 제어 설정
kp = 0.05
ki = 0.0
kd = 4.0
bot.set_pid_param(kp, ki, kd, forever=False)
kp, ki, kd = bot.get_motion_pid()
print("PID set to:", kp, ki, kd)

# ROI 범위 설정 (640 x 480)
(ROI_x1,ROI_x2), (ROI_y1,ROI_y2) = (40,600), (0,420)

def car_motion(line, angular):
    # 모터 부하 방지
    if abs(line) >= 5 or abs(angular) >= 10:
        speed_l = line / 100.0
        speed_a = -angular / 100.0
        bot.set_car_motion(speed_l, speed_a)
        return speed_l, speed_a
    else:
        bot.set_car_motion(0, 0)
        return 0, 0
    
def find_line():
    global speed, angle
    if flag == True:
        speed = 0
        if angle < 0: angle = -30
        elif angle > 0: angle = 30
    return

# 카메라 초기화
cap = cv2.VideoCapture(0)

# FPS 확인
fps = cap.get(cv2.CAP_PROP_FPS)
print(f"카메라 FPS: {fps}")

# 현재 해상도 확인
width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
print(f"카메라 해상도: {int(width)}x{int(height)}")

# 초기 변수 설정
F = L = R = r_ratio = l_ratio = 0
flag = False # 로봇이 움직이지 않음(False)
speed = angle = 0
try:
    while True:
        # 카메라에서 프레임 읽기
        ret, frame = cap.read() 
        if not ret: print("프레임을 읽을 수 없음"); break
        frame = frame[ROI_y1:ROI_y2, ROI_x1:ROI_x2] # ROI
        width , height = ROI_x2-ROI_x1, ROI_y2-ROI_y1
        x_center = width // 2
        y_center = height // 2

        gray_original = frame

        # HSV 색상 공간으로 변환
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 검은색 범위 설정
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 80])

        # 검은색만 필터링
        mask = cv2.inRange(hsv, lower_black, upper_black)

        # 마스크를 반전하여 검은색이 아닌 부분을 선택
        inverse_mask = cv2.bitwise_not(mask)

        # 원본 이미지를 복사하여 검은색 부분을 제외한 나머지를 흰색으로 채움
        filtered_image = frame.copy()
        filtered_image[inverse_mask == 255] = [255, 255, 255]  # 흰색으로 채우기

        # 결과를 흑백 이미지로 전환
        gray = cv2.cvtColor(filtered_image, cv2.COLOR_BGR2GRAY)

        # 블러를 적용하여 노이즈 제거
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # # 이진화하여 검은 선 감지(구버전)
        # _, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)

        ### 흰색 배경 탐지 조건 ###
        # 픽셀 분산 계산
        hist_variance = np.var(gray_original)
        # print(hist_variance)

        # 분산이 낮으면(즉, 픽셀 값이 비슷하면) 고정 임계값 사용
        if hist_variance < 200:
            ret, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)
        else:
            ret, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 모폴로지 연산 (팽창 -> 침식, 작은 노이즈 제거)
        kernel = np.ones((3, 3), np.uint8)
        binary_mor = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # 이진화된 이미지에서 컨투어 찾기
        contours, _ = cv2.findContours(binary_mor, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # 최소 컨투어 면적 설정
            min_contour_area = 800

            # 최소 면적 이상인 컨투어들만 필터링
            large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= min_contour_area]

            if large_contours:
                # 가장 큰 컨투어 선택 (노이즈 제거)
                largest_contour = max(contours, key=cv2.contourArea)
                cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 3)

                # 컨투어의 무게중심 계산
                M = cv2.moments(largest_contour)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])

                    # 무게중심 표시
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

                    # 방향 결정
                    x_ratio = (cx - x_center) / x_center
                    y_ratio = (cy - y_center) / y_center
                    if y_ratio < 0: y_ratio = 0

                    # speed = 10 - (abs(x_ratio) * 5)
                    speed = 5
                    angle = x_ratio * 60 # 음수: 좌회전, 양수: 우회전

                    if abs(x_ratio) < (20 / x_center):
                        direction = "F"
                        # speed = 10
                    elif x_ratio < 0: direction = "L"
                    else: direction = "R"


                    cv2.putText(frame, direction, (cx - 30, cy - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                else: find_line()
            else: find_line()
        else: find_line()

        # 카메라 화면 표시
        # cv2.imshow('bin_mor', binary_mor)
        cv2.imshow('Line Tracking', frame)
            
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): 
            bot.set_car_motion(0,0)
            break

        # Line Tracking Mode
        if key == ord('1'): 
            flag = True

        # Manual Control Mode
        if key == ord('2'): 
            flag = False
            car_motion(0,0)

        # Manual Control
        if flag == False:
            speed = angle = 0
            if (key == ord('w')) & (speed == 0): speed = 30
            elif (key != ord('w')) & (speed == 30): speed = 0
            if (key == ord('s')) & (speed == 0): speed = -30
            elif (key != ord('s')) & (speed == -30): speed = 0
            if (key == ord('a')) & (angle == 0): angle = -60
            elif (key != ord('a')) & (angle == -60): angle = 0
            if (key == ord('d')) & (angle == 0): angle = 60
            elif (key != ord('d')) & (angle == 60): angle = 0

        # 최종 모터 제어
        car_motion(speed, angle)


except Exception as e:
    print(e)
    car_motion(0,0)
    cap.release()
    cv2.destroyAllWindows()

except KeyboardInterrupt:
    car_motion(0,0)
    cap.release()
    cv2.destroyAllWindows()