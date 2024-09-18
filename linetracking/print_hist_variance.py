import cv2, subprocess, sys
import numpy as np

# ROI 범위 설정 (320 x 240)
(ROI_x1,ROI_x2), (ROI_y1,ROI_y2) = (20,300), (100,210)

# def calculate_hist_variance(image):
#     # 이미지는 그레이스케일이라고 가정
#     # 히스토그램 계산
#     hist = cv2.calcHist([image], [0], None, [256], [0, 256])

#     # 히스토그램 정규화
#     hist_norm = hist.ravel() / hist.sum()

#     # 픽셀 값 배열 (0~255)
#     bins = np.arange(256)

#     # 평균 계산
#     mean = np.sum(bins * hist_norm)

#     # 분산 계산
#     variance = np.sum(((bins - mean) ** 2) * hist_norm)

#     return variance


def calculate_pixel_variance(image):
    # 픽셀 값의 분산 계산
    variance = np.var(image)
    return variance

def main():
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

    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return

    print("카메라가 열렸습니다. 'C' 키를 눌러 현재 프레임의 히스토그램 분산을 계산합니다.")
    print("종료하려면 'Q' 키를 누르세요.")

    while True:
        # 프레임 읽기
        ret, frame = cap.read()
        if not ret:
            print("프레임을 가져올 수 없습니다.")
            break

        frame = frame[ROI_y1:ROI_y2, ROI_x1:ROI_x2] # ROI
        
        # 프레임 표시
        cv2.imshow('Camera Feed', frame)

        # 키보드 입력 받기 (1ms 대기)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c') or key == ord('C'):
            # 현재 프레임을 그레이스케일로 변환
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # # 히스토그램 분산 계산
            # hist_variance = calculate_hist_variance(gray_frame)

            # 픽셀 값의 분산 직접 계산
            pixel_variance = calculate_pixel_variance(gray_frame)

            # print(f"현재 프레임의 히스토그램 분산1: {hist_variance}")
            print(f"현재 프레임의 히스토그램 분산: {pixel_variance}")

        elif key == ord('q') or key == ord('Q'):
            # 루프 종료
            print("프로그램을 종료합니다.")
            break

    # 자원 해제
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
