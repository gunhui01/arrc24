from Transbot_Lib import Transbot
from time import time, sleep
import subprocess, sys, cv2
import numpy as np

# PID 계수
kp = 0.05
ki = 0.0
kd = 4.0

bot = Transbot()

# 데이터 수신 설정
bot.create_receive_threading()
bot.set_auto_report_state(True, forever=False)

# 조명 설정
bot.set_colorful_effect(5, speed=255, parm=255)

# bot.get_imu_state()

# PID 제어 설정
bot.set_pid_param(kp, ki, kd, forever=False)
kp, ki, kd = bot.get_motion_pid()
print("PID set to:", kp, ki, kd)

def car_motion(line, angular):
    # 모터 부하 방지
    if abs(line) >= 5 or abs(angular) >= 10:
        speed_l = line / 100.0
        speed_a = -angular / 100.0
        bot.set_car_motion(speed_l, speed_a)
        return speed_l, speed_a
    else:
        bot.set_car_motion(0, 0)
        return 0, 0