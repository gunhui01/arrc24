import cv2
import threading
import time

FOCUS_VALUE = 330  # Set focus value here
RESOLUTION_WIDTH = 1280  # Set resolution width here
RESOLUTION_HEIGHT = 720  # Set resolution height here
FPS_VALUE = 60  # Set FPS value here

CAMERA_INDICES = [0, 2]  # Use cameras with indices 0 and 2


class CameraCaptureThread(threading.Thread):
    def __init__(self, camera_index, output_file):
        super().__init__()
        self.camera_index = camera_index
        self.output_file = output_file
        self.running = False

    def run(self):
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
        if not cap.isOpened():
            print(f"Camera {self.camera_index} could not be opened.")
            return

        actual_width, actual_height, actual_fps = configure_camera_settings(cap, self.camera_index)

        # Use MJPG codec to increase compatibility
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_file, fourcc, actual_fps, (int(actual_width), int(actual_height)))

        self.running = True
        while self.running:
            ret, frame = cap.read()
            if ret:
                out.write(frame)
            else:
                print(f"Failed to grab frame from camera {self.camera_index}.")
                break

        cap.release()
        out.release()
        print(f"Camera {self.camera_index} has finished saving the video.")

    def stop(self):
        self.running = False


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


def toggle_camera_capture():
    output_files = [f'/home/bot/Desktop/output_camera_{i}.mp4' for i in CAMERA_INDICES]

    threads = {camera_index: CameraCaptureThread(camera_index, output_file) for camera_index, output_file in zip(CAMERA_INDICES, output_files)}

    try:
        while True:
            cmd = input("Enter '1' to start capturing, '2' to stop capturing, '3' to quit: ")
            if cmd == '1':
                for thread in threads.values():
                    if not thread.is_alive():
                        print(f"\nStarting recording for camera {thread.camera_index}...")
                        thread.start()
                print("\nRecording started.")
            elif cmd == '2':
                for thread in threads.values():
                    if thread.is_alive():
                        print(f"\nStopping recording for camera {thread.camera_index}...")
                        thread.stop()
                        thread.join()
                print("\nRecording stopped.")
            elif cmd == '3':
                for thread in threads.values():
                    if thread.is_alive():
                        print(f"\nStopping recording for camera {thread.camera_index}...")
                        thread.stop()
                        thread.join()
                print("\nExiting.")
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        for thread in threads.values():
            if thread.is_alive():
                thread.stop()
                thread.join()
    finally:
        for thread in threads.values():
            if thread.is_alive():
                thread.stop()
                thread.join()


if __name__ == "__main__":
    toggle_camera_capture()
