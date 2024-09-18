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
        speed_a = angular / 100.0
        bot.set_car_motion(speed_l, speed_a)
        return speed_l, speed_a
    else:
        bot.set_car_motion(0, 0)
        return 0, 0

# 카메라 초기화
cap = cv2.VideoCapture(1)

# FPS 확인
fps = cap.get(cv2.CAP_PROP_FPS)
print(f"카메라 FPS: {fps}")

# 현재 해상도 확인
width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
print(f"카메라 해상도: {int(width)}x{int(height)}")

# 직선과 y_center의 실제 교차점 계산 함수
def intersection(x1, y1, x2, y2, y_center):

    # 수직선인 경우
    if x2 - x1 == 0:
        if min(y1, y2) <= y_center <= max(y1, y2):
            return x1
        else:
            return None
    
    # 기울기가 0인 경우
    m = (y2 - y1) / (x2 - x1)
    if m == 0:
        return None
    
    # 교차점 계산
    if min(y1, y2) <= y_center <= max(y1, y2):
        b = y1 - m * x1
        x = (y_center - b) / m
        return x
    
    # 교차하지 않는 경우
    return None

# def lt_direction():
direction = None
count = 0
F = L = R = 0
r_ratio = l_ratio = 0
flag = False
try:
    while True:
        # 카메라에서 프레임 읽기
        ret, frame = cap.read() 
        if not ret: print("프레임을 읽을 수 없음"); break
        frame = frame[ROI_y1:ROI_y2, ROI_x1:ROI_x2] # ROI
        height, width = ROI_y2-ROI_y1, ROI_x2-ROI_x1

        # HSV 색상 공간으로 변환
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 검은색 범위 설정
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 255])

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

        # 오츠의 이진화 적용(테스트중, 개선있음)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 모폴로지 연산 (팽창 -> 침식, 작은 노이즈 제거)
        kernel = np.ones((3, 3), np.uint8)
        binary_mor = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        edges = cv2.Canny(binary, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 20, None, 10, 2) # 임계값 처음:10 -> 
        x_center = width // 2
        y_center = height // 2
        
        intersection_points = []

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0] # (x1, y1) : 시작점, (x2, y2) : 끝점
                cv2.line(frame, (x1,y1), (x2, y2), (0,255,0), 3) # 선 그리기 (초록색)

                x_is = intersection(x1, y1, x2, y2, y_center) # 교차점 계산
                if x_is is not None:
                    intersection_points.append((x_is, x1, y1, x2, y2))
        
        if len(intersection_points) >= 2:
            # 중앙과 가장 가까운 두 점 선택
            intersection_points.sort(key=lambda p: abs(p[0] - width // 2))
            close_intersection_point_1 = intersection_points[0]
            close_intersection_point_2 = intersection_points[1]

            if abs(close_intersection_point_1[0] - close_intersection_point_2[0]) > 50:
                avg_intersection_point = (close_intersection_point_1[0] + close_intersection_point_2[0]) / 2

                # 중심점 그리기 (빨간색)
                cv2.circle(frame, (int(close_intersection_point_1[0]), y_center), 5, (0, 0, 255), -1)
                cv2.circle(frame, (int(close_intersection_point_2[0]), y_center), 5, (0, 0, 255), -1)

                if (x_center - 20) < avg_intersection_point < (x_center + 20):
                    direction = "F"
                    F += 1
                elif avg_intersection_point > x_center:
                    direction = "R"
                    ratio = (avg_intersection_point - x_center) / x_center
                    r_ratio += ratio
                    R += 1
                elif avg_intersection_point < x_center:
                    direction = "L"
                    ratio = 1 - (avg_intersection_point / x_center)
                    l_ratio += ratio
                    L += 1
                else:
                    pass
            
            elif close_intersection_point_1[0] < x_center:
                R = True
            elif close_intersection_point_1[0] > x_center:
                L = True

            cv2.putText(frame, direction, (int(avg_intersection_point) - 30, y_center - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            dash_length = 20
            space_length = 10
            num_dashes = height // (dash_length + space_length)
            for i in range(num_dashes):
                start_y = i * (dash_length + space_length)
                end_y = start_y + dash_length
                cv2.line(frame, (int(avg_intersection_point), start_y), (int(avg_intersection_point), end_y), (0,255,255), 3)

            # cv2.imshow('blur', blurred)
            # cv2.imshow('bin', binary)
            cv2.imshow('edges', edges)
            cv2.imshow('Line Detecting', frame)
            # cv2.imshow('bin_mor', binary_mor)
            # cv2.imshow('nomask', frame)
            # cv2.imshow('black mask',filtered_image)

            count += 1
        
            if ((count % 5) == 0) & (flag == True):
                
                if (F > L) & (F > R) :
                    car_motion(10,0)
                elif (L > F) & (L > R):
                    l_ratio = l_ratio / L
                    angle = l_ratio * 100
                    speed = 10 - l_ratio * 5
                    car_motion(speed,angle)
                elif (R > L) & (R > F):
                    r_ratio = r_ratio / R
                    angle = r_ratio * -100
                    speed = 10 - r_ratio * 5
                    car_motion(speed,angle)
                elif L == True:
                    speed = 10
                    angle = -120
                    car_motion(speed,angle)
                elif R == True:
                    speed = 10
                    angle = 120
                    car_motion(speed,angle)
                else:
                    pass
                F = L = R = l_ratio = r_ratio = 0
                
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): 
                bot.set_car_motion(0,0)
                break

            if key == ord('w'): 
                flag = True

            if key == ord('s'): 
                flag = False
                bot.set_car_motion(0,0)

except Exception as e:
    print(e)
    bot.set_car_motion(0,0)
    cap.release()
    cv2.destroyAllWindows()

except KeyboardInterrupt:
    bot.set_car_motion(0,0)
    cap.release()
    cv2.destroyAllWindows()

