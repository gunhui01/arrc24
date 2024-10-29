#!/usr/bin/env python3

__author__ = "Park Gunhui"

import math, time
from rplidar import RPLidar

def multi_lidar_scan(measure_array, lidar_scan_event):
    try:
        lidar = RPLidar('/dev/ttyUSB0')
        for new_scan, quality, angle, distance in lidar.iter_measures():
            if lidar_scan_event.is_set(): break
            measure_array[0] = angle
            measure_array[1] = distance
    finally:
        lidar.stop()
        lidar.disconnect()
        print("lidar disconnected")

def determine_direction(measure_array, lidar_array):
    DIAGONAL_LENGTH = 250
    DETECT_RANGE = 150
    COS_MULTIPLY = 150

    while True:
        one_lap_measure = False
        turn_right = 0
        turn_left = 0
        while not one_lap_measure:
            if measure_array[0] > 355:
                one_lap_measure = True
            elif 5 <= measure_array[0] < 45:
                turn_left += (DIAGONAL_LENGTH + DETECT_RANGE + math.cos(math.radians(int(measure_array[1]))) * COS_MULTIPLY)
            elif 315 <= measure_array[0] < 355:
                turn_right += (DIAGONAL_LENGTH + DETECT_RANGE + math.cos(math.radians(int(measure_array[1]))) * COS_MULTIPLY)
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