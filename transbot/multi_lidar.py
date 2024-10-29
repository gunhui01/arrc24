#!/usr/bin/env python3

__author__ = "Park Gunhui"

import math, time
from rplidar import RPLidar

def multi_lidar_scan(lidar_queue, lidar_scan_event):
    try:
        lidar = RPLidar('/dev/ttyUSB0')
        for new_scan, quality, angle, distance in lidar.iter_measures():
            if lidar_scan_event.is_set(): break
            if (0 <= angle < 45) or (315 <= angle < 360):
                lidar_queue.put((int(angle), int(distance)))
    finally:
        lidar.stop()
        lidar.disconnect()
        print("lidar disconnected")

def determine_direction(lidar_queue, lidar_array):
    DIAGONAL_LENGTH = 250
    DETECT_RANGE = 150
    COS_MULTIPLY = 150

    while True:
        lap = False
        previous_angle = 0

        while not lap:
            if not lidar_queue.empty():
                lidar_value = lidar_queue.get()
                
                if lidar_value[0] < 45:
                    if lidar_value[1] < DIAGONAL_LENGTH + DETECT_RANGE + math.cos(math.radians(int(lidar_value[0]))) * COS_MULTIPLY:
                        turn_left = lidar_value[1] if lidar_value[1] < turn_left else turn_left
                else:
                    if lidar_value[1] < DIAGONAL_LENGTH + DETECT_RANGE + math.cos(math.radians(int(lidar_value[0]))) * COS_MULTIPLY:
                        turn_right = lidar_value[1] if lidar_value[1] < turn_right else turn_right
                
                if lidar_value[0] - previous_angle > 0: lap = True
                previous_angle = lidar_value[0]

        if turn_right > turn_left:
            lidar_array[0] = False
            lidar_array[1] = True
            print(lidar_array[0], lidar_array[1])
        else:
            lidar_array[0] = True
            lidar_array[1] = False
            print(lidar_array[0], lidar_array[1])

def avoid_trees(lidar_array, control_queue):
    LINE_SPEED = 10
    ANGULAR_SPEED = 60

    while True:
        turn_right = lidar_array[0]
        turn_left = lidar_array[1]
        #print(turn_right, turn_left)

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