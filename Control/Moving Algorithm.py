from Transbot_Lib import Transbot
import time
import math

#author: seyeong
#imu - Inertial Measurement Unit
#set_pid_param(kp, ki, kd, forever=False)
#set_speed_limit(line_limit, angular_limit, forever=False)
#set_imu_adjust(enable, forever=False)
#set_auto_report_state(enable, forever=False)
#clear_auto_report_data()
#reset_flash_value()
#get_accelerometer_data()
#get_gyroscope_data()
#get_motion_data()
#get_motion_pid()
#get_imu_state()

def move_forward(move_forward_length): #unit = [cm]
    move_forward_time = move_forward_length / 10
    bot.set_car_motion(0.1, 0) #velocity = [-0.45, 0.45] angular = [-2.00, 2.00] 
    time.sleep(move_forward_time)
    bot.set_car_motion(0, 0)

def move_backward(move_backward_length): #unit = [cm]
    move_backward_time = move_backward_length / 10
    bot.set_car_motion(-0.1, 0)
    time.sleep(move_backward_length)
    bot.set_car_motion(0, 0)

def turn_right(angle): #unit = [degree]
    radian_angle = angle * math.pi / 180
    turning_time = math.sqrt(2*radian_angle)
    bot.set_car_motion(0, 1)        
    time.sleep(turning_time)
    bot.set_car_motion(0, 0)

def turn_left(angle): #unit = [degree]
    radian_angle = angle * math.pi / 180
    turning_time = math.sqrt(2*radian_angle)
    bot.set_car_motion(0, -1)        
    time.sleep(turning_time)
    bot.set_car_motion(0, 0)


