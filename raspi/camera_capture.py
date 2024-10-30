
__author__ = ["Hwang Hyeonjun"]

import subprocess, sys, cv2

FOCUS_VALUE = 400  # Set focus value here
RESOLUTION_WIDTH = 1280  # Set resolution width here
RESOLUTION_HEIGHT = 720  # Set resolution height here
FPS_VALUE = 60  # Set FPS value here
CAMERA_INDICES = [0, 2]  # Use cameras with indices 0 and 2

def configure_camera_settings(cap, camera_index):
    # Set the video capture format to MJPG explicitly
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS_VALUE)

    # Set focus if supported
    focus_set = cap.set(cv2.CAP_PROP_FOCUS, FOCUS_VALUE)
    if focus_set:
        actual_focus = cap.get(cv2.CAP_PROP_FOCUS)
    else:
        actual_focus = "Not Supported"

    # Get actual resolution and FPS settings from the camera
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"\nCamera {camera_index} settings: {actual_width}x{actual_height} at {actual_fps} FPS, Focus: {actual_focus}\n")

    return actual_width, actual_height, actual_fps

### multiprocessing function ###
def camera_capture(frame_queue, camera_capture_event):
    try:
        ### Search Camera Index ###
        try:
            result = subprocess.run(['v4l2-ctl', '--list-devices'], stdout=subprocess.PIPE, check=True)
            output = result.stdout.decode()
            target_camera_name = "Razer Kiyo X"
            camera_indices = []

            lines = output.splitlines()
            for i, line in enumerate(lines):
                if target_camera_name in line:
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if '/dev/video' in next_line:
                            camera_index = int(next_line.replace('/dev/video', ''))
                            camera_indices.append(camera_index)
                            print(f"{target_camera_name} found at /dev/video{camera_index}")

            if not camera_indices:
                print("Couldn't find camera.")
                sys.exit(1)

        except subprocess.CalledProcessError as e:
            print(f"Failed to run v4l2-ctl command: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Invalid video index: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Camera not found, {e}")
            sys.exit(1)

        caps = [cv2.VideoCapture(index) for index in camera_indices]

        while not camera_capture_event.is_set():
            for idx, cap in zip(camera_indices, caps):
                if not cap.isOpened():
                    print(f"Reconnecting camera {idx} ...")
                    cap.open(idx)
                    continue
                ret, frame = cap.read()
                if not ret:
                    print(f"Cannot read frame: /dev/video{idx}")
                    continue

                if frame_queue.full():
                    _ = frame_queue.get()  # 오래된 데이터를 버림
                frame_queue.put((idx, frame))

    finally:
        for cap in caps:
            if cap.isOpened():
                cap.release()
