### 실행 전 v4l-utils 설치 필요
### sudo apt-get install v4l-utils

__author__ = "Hwang Hyeonjun"

import subprocess, sys, cv2
from time import sleep

def camera_capture(frame_queue):
    try:
        # 연결된 카메라 인덱스 확인
        try:
            result = subprocess.run(['v4l2-ctl', '--list-devices'], stdout=subprocess.PIPE)
            output = result.stdout.decode()
            camera_name = "USB Camera2"  # 찾고자 하는 카메라의 이름
            camera_index = None

            lines = output.splitlines()
            for i, line in enumerate(lines):
                if camera_name in line:
                    device_line = lines[i + 1].strip()  # 다음 줄의 공백 제거
                    camera_index = int(device_line.replace('/dev/video', ''))
                    break
            print(f"{camera_name} found at /dev/video{camera_index}")
        except Exception as e:
            print(f"Camera not found, {e}")
            sys.exit(1)

        # 카메라 초기화
        cap = cv2.VideoCapture(camera_index)

        while True:
            # 카메라에서 프레임 읽기
            ret, frame = cap.read()
            if not ret:
                print("프레임을 읽을 수 없음")
                break

            if not frame_queue.full():
                frame_queue.put(frame)

            sleep(0.01)

    finally:
        cap.release()



    # # FPS 확인
    # fps = cap.get(cv2.CAP_PROP_FPS)
    # print(f"카메라 FPS: {fps}")

    # # 현재 해상도 확인
    # width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    # height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    # print(f"카메라 해상도: {int(width)}x{int(height)}")