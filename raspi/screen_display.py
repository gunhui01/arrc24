#!/usr/bin/env python3

__author__ = "Park Gunhui"

import tkinter as tk
from PIL import Image, ImageTk
from multiprocessing import Process, Queue

CHECK_INTERVAL = 100 # ms

class ScreenDisplay:
    def __init__(self, command_share_queue, apple_count_queue):
        self.command_share_queue = command_share_queue
        self.apple_count_queue = apple_count_queue
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.bind('<Escape>', lambda e: self.root.destroy())

        self.label = tk.Label(self.root)
        self.label.pack()

        self.update_image('z') # Default image: ('z')
        self.root.after(CHECK_INTERVAL, self.check_queue)

    def check_queue(self):
        if not self.command_share_queue.empty():
            self.command = self.command_share_queue.get()
            if self.command[:7] == "screen:":
                self.update_image(self.command[7])

        if not self.apple_count_queue.empty():
            area, result = self.queue.get()
            self.update_image(area, result)

        self.root.after(CHECK_INTERVAL, self.check_queue)

    def update_image(self, filename):
        img = Image.open(f"/home/bot/arrc24/raspi/display/{filename}.png")
        self.photo = ImageTk.PhotoImage(img)
        self.label.config(image=self.photo)
        self.label.image = self.photo

    def run(self):
        self.root.mainloop()

def screen_display(image_change_queue, apple_count_queue):
    display = ScreenDisplay(image_change_queue, apple_count_queue)
    display.run()