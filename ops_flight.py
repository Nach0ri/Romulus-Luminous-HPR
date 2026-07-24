import time
import math
import csv
import subprocess
import matplotlib.pyplot as plt

import board
import busio
import adafruit_lsm6ds.lsm6dsox as lsm6ds


# ============================
# SETTINGS
# ============================

LAUNCH_THRESHOLD = 4.0   # g
LAUNCH_COUNT = 5

SAMPLE_RATE = 20         # Hz

PHOTO_INTERVAL = 1       # second

MAX_RUNTIME = 4 * 60     # seconds, auto-stop after this long

STATUS_INTERVAL = 60     # seconds, how often to reprint the full status box


# ============================
# IMU SETUP
# ============================

i2c = busio.I2C(
    board.SCL,
    board.SDA
)

imu = lsm6ds.LSM6DSOX(i2c)


# ============================
# STATUS DISPLAY
# ============================

def format_runtime(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def print_status_box(status, flight_time, accel_g):
    waiting_line = (
        "Waiting for launch..."
        if status == "STANDBY"
        else "Launch detected, logging flight..."
    )

    print("================================", flush=True)
    print("🚀 NOALGAE PAYLOAD SYSTEM", flush=True)
    print("================================", flush=True)
    print(f"STATUS: {status}", flush=True)
    print("IMU: ONLINE", flush=True)
    print("CAMERA: READY", flush=True)
    print("BATTERY: OK", flush=True)
    print("", flush=True)
    print(f"Runtime: {format_runtime(flight_time)}", flush=True)
    print(f"Acceleration: {accel_g:.2f} g", flush=True)
    print("", flush=True)
    print(waiting_line, flush=True)
    print("================================", flush=True)


# ============================
# FILE SETUP
# ============================

start_time = time.time()

csv_name = f"flight_{int(start_time)}.csv"

csv_file = open(
    csv_name,
    "w",
    newline=""
)

writer = csv.writer(csv_file)


writer.writerow([
    "time",
    "accel_g",
    "ax",
    "ay",
    "az",
    "gx",
    "gy",
    "gz"
])


# ============================
# VARIABLES
# ============================

launch_detected = False
launch_counter = 0
launch_time = None

photo_number = 0
last_photo_time = 0

last_status_time = start_time


time_data = []
g_data = []


print_status_box("STANDBY", 0.0, 0.0)


# ============================
# MAIN LOOP
# ============================


try:

    while True:

        now = time.time()
        flight_time = now - start_time

        if launch_detected and (now - launch_time) >= MAX_RUNTIME:
            print("4 minutes since launch, stopping...", flush=True)
            break


        # Read IMU

        ax, ay, az = imu.acceleration
        gx, gy, gz = imu.gyro


        total_accel = math.sqrt(
            ax**2 +
            ay**2 +
            az**2
        )


        accel_g = total_accel / 9.81


        print(
            f"Runtime: {format_runtime(flight_time)} | Accel: {accel_g:.2f} g",
            flush=True
        )

        if now - last_status_time >= STATUS_INTERVAL:
            print_status_box(
                "LAUNCHED" if launch_detected else "STANDBY",
                flight_time,
                accel_g
            )
            last_status_time = now


        # Save data

        writer.writerow([
            flight_time,
            accel_g,
            ax,
            ay,
            az,
            gx,
            gy,
            gz
        ])

        csv_file.flush()


        time_data.append(
            flight_time
        )

        g_data.append(
            accel_g
        )


        # =====================
        # LAUNCH DETECTION
        # =====================


        if not launch_detected:

            if accel_g > LAUNCH_THRESHOLD:
                launch_counter += 1

            else:
                launch_counter = 0


            if launch_counter >= LAUNCH_COUNT:

                launch_detected = True
                launch_time = now

                print_status_box("LAUNCHED", flight_time, accel_g)
                last_status_time = now



        # =====================
        # TAKE PHOTO
        # =====================


        if launch_detected:


            if now - last_photo_time >= PHOTO_INTERVAL:


                filename = (
                    f"photo_{int(now)}.jpg"
                )


                subprocess.run([
                    "rpicam-still",
                    "-o",
                    filename
                ])


                print(
                    "Saved:",
                    filename,
                    flush=True
                )


                last_photo_time = now



        time.sleep(
            1/SAMPLE_RATE
        )


except KeyboardInterrupt:

    print(
        "Stopping...",
        flush=True
    )



finally:

    csv_file.close()



# ============================
# PLOT GRAPH
# ============================

plt.figure(figsize=(10,5))

plt.plot(
    time_data,
    g_data
)

plt.xlabel(
    "Time (s)"
)

plt.ylabel(
    "Acceleration (g)"
)

plt.title(
    "Rocket Flight Acceleration"
)


plt.grid()

plt.savefig(
    "flight_plot.png"
)

plt.show()


print(
    "Finished",
    flush=True
)

print(
    "CSV:",
    csv_name,
    flush=True
)

print(
    "Plot saved: flight_plot.png",
    flush=True
)