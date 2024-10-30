#!/usr/bin/env python3

__author__ = "Park Gunhui"

import os, time

def apple_count_subscriber(apple_count_queue):
    MONITORING_DIR = "/home/bot/Desktop/shared"
    # MONITORING_DIR = "./"
    counted_area = 1

    while counted_area < 2:
        txt_files = [f for f in os.listdir(MONITORING_DIR) if f.endswith(".txt") and f.startswith(f'{counted_area}')]
        if txt_files:
            _, tmp = txt_files[0].split('_')
            count, _ = tmp.split('.')
            apple_count_queue.put(count)
            counted_area += 1
        time.sleep(1)

if __name__ == "__main__":
    apple_count_subscriber()