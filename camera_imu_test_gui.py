#!/usr/bin/env python3
"""
camera_imu_test_gui.py

Simple Tkinter GUI to preview the Pi Camera (Picamera2) and show live
LSM6DSOX IMU sensor values (accelerometer and gyroscope).

Run on the Pi after installing dependencies:
sudo python3 camera_imu_test_gui.py

Notes:
- Requires `picamera2`, `picamera2`'s dependencies, `numpy`, and `Pillow` for
  displaying frames in Tkinter. The installer script attempted to install
  Picamera2; install `python3-pil` and `python3-numpy` if missing.
- IMU uses Adafruit Blinka + CircuitPython LSM6DSOX library.
"""

import sys
import threading
import time
import traceback

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:
    print('Tkinter not available. Install python3-tk.')
    raise

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

try:
    import numpy as np
except Exception:
    np = None

# Camera imports
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except Exception:
    Picamera2 = None
    PICAMERA2_AVAILABLE = False

# IMU imports
try:
    import board
    import adafruit_lsm6dsox
    IMU_AVAILABLE = True
except Exception:
    board = None
    adafruit_lsm6dsox = None
    IMU_AVAILABLE = False


class CameraIMUGUI:
    def __init__(self, root):
        self.root = root
        root.title('Pi Camera + LSM6DSOX Test')

        self.frame_width = 320
        self.frame_height = 240

        # Camera canvas
        self.canvas = tk.Canvas(root, width=self.frame_width, height=self.frame_height)
        self.canvas.grid(row=0, column=0, rowspan=6, padx=8, pady=8)

        # IMU labels
        self.accel_vars = [tk.StringVar(value='0.0') for _ in range(3)]
        self.gyro_vars = [tk.StringVar(value='0.0') for _ in range(3)]
        self.temp_var = tk.StringVar(value='N/A')

        ttk.Label(root, text='Accel (m/s^2)').grid(row=0, column=1, sticky='w')
        for i, v in enumerate(self.accel_vars):
            ttk.Label(root, textvariable=v).grid(row=0, column=2 + i, sticky='w')

        ttk.Label(root, text='Gyro (°/s)').grid(row=1, column=1, sticky='w')
        for i, v in enumerate(self.gyro_vars):
            ttk.Label(root, textvariable=v).grid(row=1, column=2 + i, sticky='w')

        ttk.Label(root, text='Temp (C)').grid(row=2, column=1, sticky='w')
        ttk.Label(root, textvariable=self.temp_var).grid(row=2, column=2, sticky='w')

        ttk.Separator(root, orient='horizontal').grid(row=3, column=1, columnspan=3, sticky='ew', pady=6)

        self.status_var = tk.StringVar(value='Initializing...')
        ttk.Label(root, textvariable=self.status_var).grid(row=4, column=1, columnspan=3, sticky='w')

        self.quit_btn = ttk.Button(root, text='Quit', command=self.on_close)
        self.quit_btn.grid(row=5, column=1, columnspan=3, sticky='we', pady=6)

        # Camera and IMU objects
        self.picam2 = None
        self.imu = None
        self.running = True
        self.photo_image = None

        # Start device init
        self.init_devices()

        # Start periodic updates
        self.update_loop()

        root.protocol('WM_DELETE_WINDOW', self.on_close)

    def init_devices(self):
        # Initialize camera if available
        if PICAMERA2_AVAILABLE:
            try:
                self.picam2 = Picamera2()
                config = self.picam2.create_preview_configuration(main={"format": "RGB888", "size": (self.frame_width, self.frame_height)})
                self.picam2.configure(config)
                self.picam2.start()
                print('Picamera2 started')
            except Exception as e:
                print('Failed to start Picamera2:', e)
                traceback.print_exc()
                self.picam2 = None
        else:
            print('Picamera2 not installed; camera preview disabled')

        # Initialize IMU if available
        if IMU_AVAILABLE:
            try:
                i2c = board.I2C()
                self.imu = adafruit_lsm6dsox.LSM6DSOX(i2c)
                print('LSM6DSOX initialized')
            except Exception as e:
                print('Failed to initialize IMU:', e)
                traceback.print_exc()
                self.imu = None
        else:
            print('IMU libraries not available; IMU disabled')

        self.status_var.set('Ready' if (self.picam2 or self.imu) else 'No devices available')

    def update_loop(self):
        if not self.running:
            return

        # Update camera preview
        try:
            if self.picam2 is not None:
                frame = self.picam2.capture_array()
                if frame is not None and Image is not None:
                    if np is not None:
                        # Ensure uint8 and shape HxWx3
                        arr = frame.astype('uint8')
                    else:
                        arr = frame
                    img = Image.fromarray(arr)
                    self.photo_image = ImageTk.PhotoImage(image=img)
                    self.canvas.create_image(0, 0, image=self.photo_image, anchor='nw')
        except Exception:
            # Non-fatal; continue
            pass

        # Update IMU readings
        try:
            if self.imu is not None:
                accel = getattr(self.imu, 'acceleration', (0.0, 0.0, 0.0))
                gyro = getattr(self.imu, 'gyro', (0.0, 0.0, 0.0))
                temp = getattr(self.imu, 'temperature', None)

                for i in range(3):
                    self.accel_vars[i].set(f'{accel[i]:.3f}')
                    self.gyro_vars[i].set(f'{gyro[i]:.3f}')
                if temp is not None:
                    self.temp_var.set(f'{temp:.2f}')
                else:
                    self.temp_var.set('N/A')
        except Exception:
            pass

        # Schedule next update (aim ~10 FPS)
        self.root.after(100, self.update_loop)

    def on_close(self):
        self.running = False
        self.status_var.set('Shutting down...')
        # stop camera
        try:
            if self.picam2 is not None:
                self.picam2.stop()
        except Exception:
            pass
        self.root.after(200, self.root.destroy)


def main():
    root = tk.Tk()
    app = CameraIMUGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
