#!/usr/bin/env python3
"""
install_rpi_dependencies.py

Idempotent installer for Raspberry Pi Zero 2 to add required packages
for LSM6DSOX (I2C IMU) and Pi Camera Module 2 (libcamera / Picamera2).

Run with: sudo python3 install_rpi_dependencies.py

This script performs apt updates/installs and pip3 installs, attempts to
enable I2C and camera via raspi-config if available, and adds the current
user to the i2c and video groups.
"""

import os
import shutil
import subprocess
import sys


def is_root():
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


def run(cmd, check=True):
    print('\n$ ' + ' '.join(cmd))
    res = subprocess.run(cmd)
    if check and res.returncode != 0:
        print(f"Command failed: {' '.join(cmd)} (exit {res.returncode})")
        sys.exit(res.returncode)
    return res.returncode


def apt_install(packages):
    if not packages:
        return
    sudo = [] if is_root() else ['sudo']
    run(sudo + ['apt', 'update'])
    run(sudo + ['apt', 'install', '-y'] + packages)


def pip_install(packages):
    if not packages:
        return
    pip_cmd = shutil.which('pip3') or shutil.which('pip')
    if not pip_cmd:
        print('pip3 not found, installing python3-pip via apt...')
        apt_install(['python3-pip'])
        pip_cmd = shutil.which('pip3') or shutil.which('pip')
    run([pip_cmd, 'install', '--upgrade'] + packages)


def enable_services():
    # Attempt to enable camera and i2c using raspi-config nonint (if available)
    raspi = shutil.which('raspi-config')
    sudo = [] if is_root() else ['sudo']
    if raspi:
        print('\nAttempting to enable I2C and camera using raspi-config...')
        # 0 = enable
        run(sudo + ['raspi-config', 'nonint', 'do_i2c', '0'], check=False)
        run(sudo + ['raspi-config', 'nonint', 'do_camera', '0'], check=False)
    else:
        print('\nraspi-config not found; please enable I2C and camera with `sudo raspi-config`')

    # Add user to i2c and video groups so Python can access devices
    user = os.environ.get('SUDO_USER') or os.environ.get('USER') or ''
    if user:
        print(f'Adding user {user} to groups: i2c, video')
        run(sudo + ['usermod', '-aG', 'i2c,video', user], check=False)


def main():
    print('Installer for LSM6DSOX and Pi Camera Module 2 (Raspberry Pi Zero 2)')

    apt_packages = [
        'python3-venv',
        'python3-pip',
        'i2c-tools',
        'python3-smbus',
        'libcamera-apps',
        'python3-picamera2'
    ]

    pip_packages = [
        'adafruit-blinka',
        'adafruit-circuitpython-lsm6dsox',
        'smbus2'
    ]

    print('\nInstalling apt packages...')
    apt_install(apt_packages)

    print('\nInstalling pip packages...')
    pip_install(pip_packages)

    # Some systems may not supply python3-picamera2 via apt; try pip as fallback
    if shutil.which('python3-picamera2') is None:
        print('\nEnsuring Picamera2 python package is present (fallback to pip)...')
        pip_install(['picamera2'])

    enable_services()

    print('\nInstallation complete. Reboot is recommended for changes to take effect.')
    print('Reboot now with: sudo reboot')


if __name__ == '__main__':
    main()
