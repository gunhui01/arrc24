__author__ = "Park Gunhui"

import asyncio
import cv2
import numpy as np
from rplidar import RPLidar

CANVAS_SIZE = 650
HALF_CANVAS_SIZE = CANVAS_SIZE // 2

lidar = RPLidar("/dev/ttyUSB0")
canvas = np.zeros((CANVAS_SIZE, CANVAS_SIZE, 3), dtype=np.uint8)

async def draw_circles(scan):
    for (_, angle, distance) in scan:
        x = int(np.sin(np.radians(angle)) * (distance / 10) + HALF_CANVAS_SIZE)
        y = int(np.cos(np.radians(angle)) * (distance / 10) + HALF_CANVAS_SIZE)

        cv2.circle(canvas, (x, y), 3, (0, 0, 255), -1)

'''
try:
    for i, scan in enumerate(lidar.iter_measures()):
        if (i % 10 == 0) and int(scan[3]):
            x = int(np.sin(np.radians(scan[2])) * (scan[3] / 10) + HALF_CANVAS_SIZE)
            y = int(np.cos(np.radians(scan[2])) * (scan[3] / 10) + HALF_CANVAS_SIZE)

            cv2.circle(canvas, (x, y), 3, (0, 0, 255), -1)
            #flip_canvas = cv2.flip(canvas, 0)

            cv2.imshow("LiDAR Visualizer", canvas)
            cv2.waitKey(1)
except KeyboardInterrupt:
    lidar.stop()
    lidar.disconnect()
    cv2.destroyAllWindows()
'''

try:
    for i, scan in enumerate(lidar.iter_scans()):
        asyncio.run(draw_circles(scan))
        flip_canvas = cv2.flip(canvas, 0)
        cv2.imshow("LiDAR Visualizer", flip_canvas)
        cv2.waitKey(1)
        canvas = np.zeros((CANVAS_SIZE, CANVAS_SIZE, 3), dtype=np.uint8)
except KeyboardInterrupt:
    lidar.stop()
    lidar.disconnect()
    cv2.destroyAllWindows()