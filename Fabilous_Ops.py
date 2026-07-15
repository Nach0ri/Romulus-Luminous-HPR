import time
import math
import csv
from mpu6050 import mpu6050

# ---------------------------
# Settings
# ---------------------------
LAUNCH_THRESHOLD = 3.0      
LAUNCH_COUNT = 5            # consecutive readings

LANDING_ACCEL_MIN = 0.9
LANDING_ACCEL_MAX = 1.1
LANDING_GYRO_MAX = 5.0      # deg/s
LANDING_COUNT = 100         # ~5 sec at 20Hz

# ---------------------------
# IMU Setup
# ---------------------------
sensor = mpu6050(0x68)

recording = False
launch_counter = 0
landing_counter = 0

csv_file = None
csv_writer = None

print("Waiting for launch...")

while True:

    accel = sensor.get_accel_data()
    gyro = sensor.get_gyro_data()

    ax = accel['x']
    ay = accel['y']
    az = accel['z']

    gx = gyro['x']
    gy = gyro['y']
    gz = gyro['z']

    total_accel = math.sqrt(ax**2 + ay**2 + az**2)
    total_gyro = math.sqrt(gx**2 + gy**2 + gz**2)

    # ---------------------------
    # Launch Detection
    # ---------------------------
    if not recording:

        if total_accel > LAUNCH_THRESHOLD:
            launch_counter += 1
        else:
            launch_counter = 0

        if launch_counter >= LAUNCH_COUNT:

            print("LAUNCH DETECTED")

            csv_file = open("flight_data.csv", "w", newline="")
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow([
                "time",
                "ax", "ay", "az",
                "gx", "gy", "gz",
                "total_accel",
                "total_gyro"
            ])

            recording = True
            launch_time = time.time()

    # ---------------------------
    # Recording
    # ---------------------------
    else:

        timestamp = time.time() - launch_time

        csv_writer.writerow([
            timestamp,
            ax, ay, az,
            gx, gy, gz,
            total_accel,
            total_gyro
        ])

        print(
            f"REC | t={timestamp:.1f}s "
            f"A={total_accel:.2f}g "
            f"G={total_gyro:.2f}"
        )

        # ---------------------------
        # Landing Detection
        # ---------------------------
        if (
            LANDING_ACCEL_MIN <= total_accel <= LANDING_ACCEL_MAX
            and total_gyro < LANDING_GYRO_MAX
        ):
            landing_counter += 1
        else:
            landing_counter = 0

        if landing_counter >= LANDING_COUNT:

            print("LANDING DETECTED")
            print("Stopping recording...")

            csv_file.close()

            break

    time.sleep(0.05)   # 20 Hz

print("Flight data saved to flight_data.csv")