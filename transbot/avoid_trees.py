#!/usr/bin/env python3

__author__ = "Park Gunhui"
__credits__ = ["Lee Donghyun", "Hwang Hyeonjun", "Noh Minhyeok"]

import math, time
from rplidar import RPLidar

def lidar_scan(lidar_array, lidar_scan_event):
    try:
        DIAGONAL_LENGTH = 250
        DETECT_RANGE = 150
        COS_MULTIPLY = 150
        turn_right = False
        turn_left = False

        lidar = RPLidar('/dev/ttyUSB0')

        for new_scan, quality, angle, distance in lidar.iter_measures():
            if lidar_scan_event.is_set(): break
            if distance:
                if 315 <= angle < 360:
                    turn_right = distance < (DIAGONAL_LENGTH + DETECT_RANGE + math.cos(math.radians(int(angle))) * COS_MULTIPLY)
                elif 0 <= angle < 45:
                    turn_left = distance < (DIAGONAL_LENGTH + DETECT_RANGE + math.cos(math.radians(int(angle))) * COS_MULTIPLY)
                lidar_array[0] = turn_right
                lidar_array[1] = turn_left
    finally:
        lidar.stop()
        lidar.disconnect()

def avoid_trees(lidar_array, control_queue):
    LINE_SPEED = 10
    ANGULAR_SPEED = 100

    while True:
        turn_right = lidar_array[0]
        turn_left = lidar_array[1]
        print(turn_right, turn_left)

        if turn_right and turn_left:
            control_queue.put((LINE_SPEED, 0))
        elif turn_right:
            control_queue.put((LINE_SPEED, ANGULAR_SPEED))
            time.sleep(0.025)
        elif turn_left:
            control_queue.put((LINE_SPEED, -ANGULAR_SPEED))
            time.sleep(0.025)
        else:
            control_queue.put((LINE_SPEED, 0))
        time.sleep(0.01)