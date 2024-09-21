
__author__ = "Hwang Hyeonjun"

## 변수 설정 ##

# ROI 범위 설정 (원본: 320 x 240)
(ROI_x1,ROI_x2), (ROI_y1,ROI_y2) = (20,300), (100,210)

# 히스토그램 분산 출력 (기본값: False)
hist_variance_print = False
hist_variance_threshold = 200 # 흰색 바탕에 검은 선이 약간 걸치는 값 확인 후 설정

# 최소 컨투어 면적 설정 (기본값: 800)
min_contour_area = 800

# 검은색 탐지 기준 명도값 설정 (기본값: 80, 최대: 255)
brightness_threshold = 80


## 실행 코드 ##

from time import time, sleep
import cv2
import numpy as np

def find_line():
    global speed, angle
    speed = 0
    if angle < 0: angle = -60
    elif angle > 0: angle = 60
    return

# 메인 함수
def line_tracing(frame_queue, control_queue, flag_queue):
    # 초기 변수 설정
    flag = True # 로봇이 움직이지 않음 = False)
    speed = angle = 0
    find_line_count = 0

    try:
        while True:
            if not frame_queue.empty():
                # 큐에서 프레임 가져오기
                frame = frame_queue.get()
                frame = cv2.resize(frame, dsize=(320,240), interpolation=cv2.INTER_LINEAR)
                frame = frame[ROI_y1:ROI_y2, ROI_x1:ROI_x2] # ROI
                frame_original = frame
                width , height = ROI_x2-ROI_x1, ROI_y2-ROI_y1
                x_center = width // 2
                y_center = height // 2

                # HSV 색상 공간으로 변환
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                # 검은색 범위 설정
                lower_black = np.array([0, 0, 0])
                upper_black = np.array([180, 255, brightness_threshold])

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

                ### 흰색 배경 탐지 조건 ###
                # 픽셀 분산 계산
                hist_variance = np.var(frame_original)
                if hist_variance_print == True:
                    print(hist_variance)

                # 분산이 낮으면(즉, 픽셀 값이 비슷하면) 고정 임계값 사용
                if hist_variance < hist_variance_threshold:
                    ret, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)
                else:
                    ret, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

                # 모폴로지 연산 (팽창 -> 침식, 작은 노이즈 제거)
                kernel = np.ones((3, 3), np.uint8)
                binary_mor = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

                # 이진화된 이미지에서 컨투어 찾기
                contours, _ = cv2.findContours(binary_mor, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                is_contour_exist = False

                if contours:
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
                            speed = 10
                            angle = x_ratio * 60 # 음수: 좌회전, 양수: 우회전

                            if abs(x_ratio) < (20 / x_center):
                                direction = "F"
                                # speed = 10
                            elif x_ratio < 0: direction = "L"
                            else: direction = "R"


                            cv2.putText(frame, direction, (cx - 30, cy - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            find_line_count = 0
                            is_contour_exist = True

                if (is_contour_exist == False) & (flag == True):
                    if find_line_count == 0:
                        now = time()
                    find_line()
                    find_line_count += 1
                    if time() >= now + 2:
                        print(f"Stop zone detected")
                        control_queue.put((0, -angle))
                        sleep(2.8)
                        break

                # 카메라 화면 표시
                cv2.imshow('Line Tracking', frame)
                    
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    control_queue.put((speed, angle))
                    break

                # 최종 모터 제어
                control_queue.put((speed, angle))
                sleep(0.01)

    except Exception as e: print(e)
    finally:
        control_queue.put((0, 0))
        flag_queue.put(True)
        cv2.destroyAllWindows()