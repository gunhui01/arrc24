#!/usr/bin/env python3

__author__ = "Park Gunhui"

import tkinter as tk
from PIL import Image, ImageTk
from multiprocessing import Process, Queue

CHECK_INTERVAL = 100 # ms

class ScreenDisplay:
    def __init__(self, command_share_queue, image_change_queue):
        self.command_share_queue = command_share_queue
        self.image_change_queue = image_change_queue
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.bind('<Escape>', lambda e: self.root.destroy())

        self.label = tk.Label(self.root)
        self.label.pack()

        self.update_image("0", "0") # Default image: ("0", "0")
        self.root.after(CHECK_INTERVAL, self.check_queue)

    def check_queue(self):
        if not self.command_share_queue.empty():
            self.command = self.command_share_queue.get()
            if self.command[:7] == "screen:":
                self.update_image(self.command[7], self.command[9])

        if not self.image_change_queue.empty():
            area, result = self.queue.get()
            self.update_image(area, result)
        
        self.root.after(CHECK_INTERVAL, self.check_queue)

    def update_image(self, area, result):
        img = Image.open(f"./display/{area}/{result}.png")
        self.photo = ImageTk.PhotoImage(img)
        self.label.config(image=self.photo)
        self.label.image = self.photo

    def run(self):
        self.root.mainloop()

def screen_display(command_share_queue, image_change_queue):
    display = ScreenDisplay(command_share_queue, image_change_queue)
    display.run()