#!/usr/bin/env python3

__author__ = "Park Gunhui"
__credits__ = ["Lee Donghyun", "Hwang Hyeonjun", "Noh Minhyeok"]

import asyncio, math
from Transbot_Lib import Transbot
from rplidar import RPLidar

TURN_RIGHT = False
TURN_LEFT = False
DIAGONAL_LENGTH = 250
DETECT_RANGE = 150
COS_MULTIPLY = 150
LINE_SPEED = 10
ANGULAR_SPEED = 100

def car_motion(line, angular):
    if abs(line) >= 5 or abs(angular) >= 10:
        speed_l = line / 100.0
        speed_a = -angular / 100.0
        bot.set_car_motion(speed_l, speed_a)
    else:
        bot.set_car_motion(0, 0)

def lidar_scan():
    global TURN_RIGHT, TURN_LEFT
    for new_scan, quality, angle, distance in lidar.iter_measures():
        if distance:
            if 315 <= angle < 360:
                TURN_RIGHT = distance < (DIAGONAL_LENGTH + DETECT_RANGE + math.cos(math.radians(int(angle))) * COS_MULTIPLY)
            elif 0 <= angle < 45:
                TURN_LEFT = distance < (DIAGONAL_LENGTH + DETECT_RANGE + math.cos(math.radians(int(angle))) * COS_MULTIPLY)

async def robot_control():
    while True:
        if TURN_LEFT and TURN_RIGHT:
            car_motion(LINE_SPEED, 0)
        elif TURN_RIGHT:
            car_motion(LINE_SPEED, ANGULAR_SPEED)
            await asyncio.sleep(0.025)
        elif TURN_LEFT:
            car_motion(LINE_SPEED, -ANGULAR_SPEED)
            await asyncio.sleep(0.025)
        else:
            car_motion(LINE_SPEED, 0)
        await asyncio.sleep(0.01)

async def main():
    control_task = asyncio.create_task(robot_control())
    await control_task

if __name__ == "__main__":
    bot = Transbot()
    lidar = RPLidar('/dev/ttyUSB0')

    print(lidar.get_info())
    print(lidar.get_health())

    try:
        lidar_scan_thread = asyncio.get_event_loop().run_in_executor(None, lidar_scan)
        asyncio.run(main())
    except KeyboardInterrupt:
        car_motion(0, 0)
        lidar.stop()
        lidar.disconnect()
        del bot
    except Exception as e:
        print(f"Error: {e}")
        car_motion(0, 0)
        lidar.stop()
        lidar.disconnect()
        del bot