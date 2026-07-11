#!/usr/bin/env python3
"""
launch_capture.py

Monitors the LSM6DSOX IMU once per second for a magnitude >= 3G and,
when triggered, uses the Pi Camera (Picamera2) to take one picture per
second for 120 seconds, saving files with timestamps.

This script will attempt to run `check_headless_requirements.py` before
initializing hardware; if the check fails the script exits early.

Run on the Pi with:
sudo python3 launch_capture.py

Notes:
- The script will try to set a larger accelerometer range if supported.
- It exits after completing the 120s capture sequence. Modify if you
  want continuous monitoring.
"""

import math
import time
import os
import sys
import traceback
import subprocess
from pathlib import Path

# Run the headless requirements checker first (if present)
checker = Path(__file__).with_name('check_headless_requirements.py')
# Allow bypassing the headless checker with environment variable or CLI flag
# - set SKIP_HEADLESS_CHECK=1 or pass --skip-check on the command line
skip_check_env = os.environ.get('SKIP_HEADLESS_CHECK') in ('1', 'true', 'True')
skip_check_arg = '--skip-check' in sys.argv
if checker.exists() and not (skip_check_env or skip_check_arg):
    rc = subprocess.run([sys.executable, str(checker)]).returncode
    if rc != 0:
        print('Headless requirements check failed; aborting.')
        sys.exit(rc)
elif skip_check_env or skip_check_arg:
    print('Skipping headless requirements check (SKIP_HEADLESS_CHECK set or --skip-check present)')

# Hardware modules will be imported/initialized later; initialize flags here
IMU_OK = False
PICAMERA_OK = False
PIL_OK = False
board = None
adafruit_lsm6dsox = None
Picamera2 = None
Image = None


G = 9.80665
THRESHOLD_G = 3.0
THRESHOLD = THRESHOLD_G * G


def init_imu():
    try:
        import board as _board
        import adafruit_lsm6dsox as _lsm
    except Exception:
        print('IMU libraries not available (board/adafruit_lsm6dsox).')
        return None
    try:
        i2c = _board.I2C()
        imu = _lsm.LSM6DSOX(i2c)
        # Try to set a wider accel range if supported (common attribute)
        try:
            if hasattr(_lsm, 'RANGE_8G'):
                imu.accelerometer_range = _lsm.RANGE_8G
                print('Set accelerometer range to 8G')
            elif hasattr(_lsm, 'RANGE_16G'):
                imu.accelerometer_range = _lsm.RANGE_16G
                print('Set accelerometer range to 16G')
        except Exception:
            pass
        return imu
    except Exception:
        print('Failed to initialize IMU:')
        traceback.print_exc()
        return None


def init_camera(preview_size=(640, 480), still_size=(1920, 1080)):
    try:
        from picamera2 import Picamera2 as _Picamera2
    except Exception:
        print('Picamera2 not available; cannot capture images.')
        return None
    try:
        picam2 = _Picamera2()
        config = picam2.create_still_configuration(main={"format": "RGB888", "size": still_size})
        picam2.configure(config)
        picam2.start()
        # warm up
        time.sleep(0.2)
        return picam2
    except Exception:
        print('Failed to initialize Picamera2:')
        traceback.print_exc()
        return None


def capture_file(picam2, filename):
    """Capture a still to `filename`. Uses capture_file if present,
    otherwise falls back to capture_array + PIL save (if available)."""
    try:
        if hasattr(picam2, 'capture_file'):
            picam2.capture_file(filename)
            return True
        else:
            arr = picam2.capture_array()
            if arr is None:
                return False
            if not PIL_OK:
                print('Pillow not available; cannot save array to file.')
                return False
            img = Image.fromarray(arr)
            img.save(filename)
            return True
    except Exception:
        traceback.print_exc()
        return False


def monitor_and_capture(poll_interval=1.0, capture_interval=1.0, capture_duration=120):
    imu = init_imu()
    if imu is None:
        print('IMU not initialized; exiting.')
        return

    picam2 = init_camera()
    if picam2 is None:
        print('Camera not initialized; exiting.')
        return

    print(f'Monitoring IMU at {poll_interval}s intervals for > {THRESHOLD_G}G ({THRESHOLD:.2f} m/s^2)')
    try:
        while True:
            try:
                accel = imu.acceleration  # tuple (x,y,z) in m/s^2
            except Exception:
                print('Failed to read acceleration; retrying...')
                accel = (0.0, 0.0, 0.0)

            mag = math.sqrt(accel[0]**2 + accel[1]**2 + accel[2]**2)
            print(f'Accel magnitude: {mag:.3f} m/s^2')
            if mag >= THRESHOLD:
                print('Threshold exceeded! Starting capture sequence...')
                # create output dir
                outdir = 'impact_captures'
                os.makedirs(outdir, exist_ok=True)
                frames = int(capture_duration / capture_interval)
                for i in range(frames):
                    timestamp = time.strftime('%Y%m%d_%H%M%S')
                    filename = os.path.join(outdir, f'impact_{timestamp}_{i:03d}.jpg')
                    ok = capture_file(picam2, filename)
                    print(f'Captured {filename}: {"OK" if ok else "FAIL"}')
                    time.sleep(capture_interval)
                print('Capture sequence complete; exiting.')
                break

            time.sleep(poll_interval)
    finally:
        try:
            if picam2 is not None:
                picam2.stop()
        except Exception:
            pass


def main():
    monitor_and_capture()


if __name__ == '__main__':
    main()
