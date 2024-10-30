import numpy as np
import cv2
from transbot.bot_control import bot_control

def move_robot_to_marker_center(frame, corners, ids, camera_matrix, dist_coeffs, desired_distance=15):
    # 이미지의 중심 계산
    frame_center_x = frame.shape[1] / 2

    for i, corner in enumerate(corners):
        if ids[i][0] == 10:  # ID가 10번인 마커만 인식
            # Aruco 마커의 중심 계산
            marker_center_x = int(np.mean(corner[0][:, 0]))

            # 카메라와 마커 사이의 거리 계산
            rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(corner, 0.02, camera_matrix, dist_coeffs)
            distance = tvec[0][0][2] * 100  # m -> cm 변환

            # X축 오차 계산
            error_x = marker_center_x - frame_center_x

            # 각속도 설정 (오차에 따라)
            angular_speed = -10 if error_x > 10 else 10 if error_x < -10 else 0

            # 선속도 설정 (거리와 각속도에 따라)
            if distance > desired_distance + 1:
                line_speed = 100  # 지정된 속도로 이동
            else:
                line_speed = 0  # 목표 거리 도달 시 멈춤

            # 로봇 제어
            bot_control(line_speed, angular_speed)
            print(f"Moving to marker {ids[i][0]} - Line speed: {line_speed}, Angular speed: {angular_speed}, Distance: {distance:.2f} cm")

def detect_and_move_to_marker(aruco_dict_type, camera_matrix, dist_coeffs):
    # USB 카메라 연결
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Aruco 마커 검출
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_type)
        parameters = cv2.aruco.DetectorParameters()
        corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

        # ID가 10번인 마커가 있으면 이동 수행
        if ids is not None:
            if 10 in ids:
                # 마커 중심으로 이동하도록 제어
                move_robot_to_marker_center(frame, corners, ids, camera_matrix, dist_coeffs)

            # 마커 검출된 경우, 검출된 마커를 화면에 표시
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
        
        cv2.imshow("Aruco Marker Detection", frame)

        if cv2.waitKey(1) == ord('q'):  # 'q' 키를 누르면 종료
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # 아루코 마커 타입 설정 및 카메라 파라미터 불러오기
    aruco_dict_type = cv2.aruco.DICT_5X5_250

    with np.load('camera_calibration.npz') as data:
        camera_matrix = data['camera_matrix']
        dist_coeffs = data['distortion_coefficients']  # 왜곡 계수 로드

    # 아루코 마커 인식 및 로봇 이동 수행
    detect_and_move_to_marker(aruco_dict_type, camera_matrix, dist_coeffs)