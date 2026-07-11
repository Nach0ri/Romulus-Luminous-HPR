#!/usr/bin/env python3
"""
newscript_imu.py

Monitors the LSM6DSOX IMU and, once launch acceleration is detected
(magnitude >= threshold, default 3G), starts logging high-rate IMU data
(accel, gyro, temp) to a timestamped CSV file for the flight.

This script will attempt to run `check_headless_requirements.py` before
initializing hardware; if the check fails the script exits early.

Run on the Pi with:
    sudo python3 newscript_imu.py

Options:
    --threshold-g FLOAT   launch trigger threshold in Gs (default 3.0)
    --rate-hz FLOAT       logging sample rate once triggered (default 50)
    --duration SECONDS    how long to log after launch is detected (default 180)
    --skip-check          skip the headless requirements check
"""

import argparse
import csv
import math
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

G = 9.80665


def run_headless_check(skip):
    checker = Path(__file__).with_name('check_headless_requirements.py')
    skip_env = os.environ.get('SKIP_HEADLESS_CHECK') in ('1', 'true', 'True')
    if checker.exists() and not (skip or skip_env):
        rc = subprocess.run([sys.executable, str(checker)]).returncode
        if rc != 0:
            print('Headless requirements check failed; aborting.')
            sys.exit(rc)
    elif skip or skip_env:
        print('Skipping headless requirements check')


def init_imu():
    try:
        import board
        import adafruit_lsm6dsox
    except Exception:
        print('IMU libraries not available (board/adafruit_lsm6dsox).')
        return None
    try:
        i2c = board.I2C()
        imu = adafruit_lsm6dsox.LSM6DSOX(i2c)
        try:
            if hasattr(adafruit_lsm6dsox, 'RANGE_8G'):
                imu.accelerometer_range = adafruit_lsm6dsox.RANGE_8G
                print('Set accelerometer range to 8G')
            elif hasattr(adafruit_lsm6dsox, 'RANGE_16G'):
                imu.accelerometer_range = adafruit_lsm6dsox.RANGE_16G
                print('Set accelerometer range to 16G')
        except Exception:
            pass
        return imu
    except Exception:
        print('Failed to initialize IMU:')
        traceback.print_exc()
        return None


def wait_for_launch(imu, threshold, poll_interval=0.1):
    print(f'Waiting for launch: acceleration magnitude >= {threshold:.2f} m/s^2')
    while True:
        try:
            accel = imu.acceleration
        except Exception:
            print('Failed to read acceleration; retrying...')
            time.sleep(poll_interval)
            continue

        mag = math.sqrt(accel[0] ** 2 + accel[1] ** 2 + accel[2] ** 2)
        if mag >= threshold:
            print(f'Launch detected! magnitude={mag:.2f} m/s^2')
            return
        time.sleep(poll_interval)


def record_flight(imu, duration, rate_hz, outdir='flight_logs'):
    os.makedirs(outdir, exist_ok=True)
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(outdir, f'flight_{timestamp}.csv')
    period = 1.0 / rate_hz

    print(f'Recording flight data to {filename} for {duration}s at {rate_hz}Hz')
    start = time.monotonic()
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['elapsed_s', 'accel_x', 'accel_y', 'accel_z', 'accel_mag_g',
                          'gyro_x', 'gyro_y', 'gyro_z', 'temp_c'])
        while True:
            loop_start = time.monotonic()
            elapsed = loop_start - start
            if elapsed >= duration:
                break

            try:
                accel = imu.acceleration
                gyro = imu.gyro
                temp = getattr(imu, 'temperature', None)
            except Exception:
                time.sleep(period)
                continue

            mag_g = math.sqrt(accel[0] ** 2 + accel[1] ** 2 + accel[2] ** 2) / G
            writer.writerow([f'{elapsed:.3f}', accel[0], accel[1], accel[2], f'{mag_g:.3f}',
                              gyro[0], gyro[1], gyro[2], temp])

            sleep_time = period - (time.monotonic() - loop_start)
            if sleep_time > 0:
                time.sleep(sleep_time)

    print('Recording complete:', filename)
    return filename


def parse_args():
    parser = argparse.ArgumentParser(description='Monitor IMU and log data once rocket launch is detected.')
    parser.add_argument('--threshold-g', type=float, default=3.0, help='launch trigger threshold in Gs')
    parser.add_argument('--rate-hz', type=float, default=50.0, help='logging sample rate once triggered')
    parser.add_argument('--duration', type=float, default=180.0, help='seconds to log after launch is detected')
    parser.add_argument('--skip-check', action='store_true', help='skip the headless requirements check')
    return parser.parse_args()


def main():
    args = parse_args()
    run_headless_check(args.skip_check)

    imu = init_imu()
    if imu is None:
        print('IMU not initialized; exiting.')
        sys.exit(1)

    threshold = args.threshold_g * G
    wait_for_launch(imu, threshold)
    record_flight(imu, args.duration, args.rate_hz)


if __name__ == '__main__':
    main()
