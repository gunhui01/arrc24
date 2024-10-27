#!/usr/bin/env python3

__author__ = "Park Gunhui"

import time
from multiprocessing import Process, Queue

from screen_display import screen_display
from command_receiver import command_receiver

def main():
    display_info_queue = Queue()
    command_share_queue = Queue()

    screen_display_process = Process(target=screen_display, args=(command_share_queue, display_info_queue))
    command_receiver_process = Process(target=command_receiver, args=(command_share_queue,))

    screen_display_process.start()
    command_receiver_process.start()

    # display_info_queue.put(("1", "1"))

if __name__ == "__main__":
    main()