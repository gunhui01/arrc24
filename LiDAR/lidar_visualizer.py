#!/usr/bin/env python3

__author__ = "Park Gunhui"
__credits__ = ["Kim Hyosung"]

import asyncio
import cv2
import numpy as np
from rplidar import RPLidar

CANVAS_SIZE = 700
HALF_CANVAS_SIZE = CANVAS_SIZE // 2
SCALE = HALF_CANVAS_SIZE / 6000

lidar = RPLidar("/dev/ttyUSB0")
canvas = np.zeros((CANVAS_SIZE, CANVAS_SIZE, 3), dtype=np.uint8)

async def draw_circles(scan):
    for _, angle, distance in scan:
        x = int(np.sin(np.radians(angle)) * (distance * SCALE) + HALF_CANVAS_SIZE)
        y = int(np.cos(np.radians(angle)) * (distance * SCALE) + HALF_CANVAS_SIZE)

        cv2.circle(canvas, (x, y), 3, (0, 0, 255), -1)

if __name__ == "__main__":
    print("Press Ctrl+C to quit")
    while True:
        try:
            for scan in lidar.iter_scans():
                asyncio.run(draw_circles(scan))
                flip_canvas = cv2.flip(canvas, 0)
                cv2.imshow("LiDAR Visualizer", flip_canvas)
                cv2.waitKey(1)
                canvas = np.zeros((CANVAS_SIZE, CANVAS_SIZE, 3), dtype=np.uint8)
        except KeyboardInterrupt:
            lidar.stop()
            lidar.disconnect()
            cv2.destroyAllWindows()
            break
        except Exception:
            lidar.reset()