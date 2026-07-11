#!/usr/bin/env python3
"""
check_headless_requirements.py

Checks that the Pi has the expected libraries and device nodes for
headless operation with LSM6DSOX + Picamera2. Exits with 0 on success
and non-zero on failure.
"""

import importlib.util
import shutil
import sys
import os


def has_module(name):
    return importlib.util.find_spec(name) is not None


def check_devices():
    issues = []

    # Check I2C device
    if not os.path.exists('/dev/i2c-1'):
        issues.append('I2C device /dev/i2c-1 not present (I2C may be disabled)')

    # Check camera device(s) - libcamera typically creates /dev/video0
    if not os.path.exists('/dev/video0'):
        # fallback check for vchiq
        if not os.path.exists('/dev/vchiq'):
            # also check for libcamera-hello command
            if shutil.which('libcamera-hello') is None:
                issues.append('Camera device not found (/dev/video0 or /dev/vchiq) and libcamera-hello missing')

    return issues


def check_groups():
    issues = []
    user = os.environ.get('SUDO_USER') or os.environ.get('USER')
    if user:
        try:
            import grp
            groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
            # Also include primary group
            import pwd
            primary = pwd.getpwnam(user).pw_gid
            try:
                groups.append(grp.getgrgid(primary).gr_name)
            except Exception:
                pass
            if 'i2c' not in groups:
                issues.append(f'user {user} not in group i2c')
            if 'video' not in groups:
                issues.append(f'user {user} not in group video')
        except Exception:
            pass
    return issues


def check_python_packages():
    required = [
        ('picamera2', 'Picamera2 (picamera2)'),
        ('adafruit_lsm6dsox', 'Adafruit CircuitPython LSM6DSOX (adafruit-circuitpython-lsm6dsox)'),
        ('board', 'Adafruit Blinka (board)'),
    ]
    optional = [
        ('PIL', 'Pillow (PIL / Pillow)'),
        ('numpy', 'numpy'),
    ]
    issues = []
    for mod, desc in required:
        if not has_module(mod):
            issues.append(f'missing Python module: {desc} (import name: {mod})')
    for mod, desc in optional:
        if not has_module(mod):
            issues.append(f'optional but recommended missing module: {desc} (import name: {mod})')
    return issues


def check_commands():
    cmds = ['libcamera-hello']
    issues = []
    for c in cmds:
        if shutil.which(c) is None:
            issues.append(f'command not found: {c} (install libcamera-apps)')
    return issues


def check_requirements(verbose=True):
    problems = []
    problems += check_python_packages()
    problems += check_commands()
    problems += check_devices()
    problems += check_groups()

    if verbose:
        if not problems:
            print('All headless requirements look OK')
        else:
            print('Headless requirements check found issues:')
            for p in problems:
                print(' -', p)
            print('\nSuggested fixes:')
            print(' - Enable I2C and Camera via: sudo raspi-config (Interfaces)')
            print(' - Install Picamera2 and libcamera-apps: sudo apt install -y libcamera-apps python3-picamera2')
            print(' - Install CircuitPython libs: pip3 install adafruit-blinka adafruit-circuitpython-lsm6dsox')
            print(' - Install Pillow/numpy if needed: pip3 install Pillow numpy')
            print(' - Add user to groups: sudo usermod -aG i2c,video <user>')

    return len(problems) == 0


if __name__ == '__main__':
    ok = check_requirements(verbose=True)
    sys.exit(0 if ok else 2)
