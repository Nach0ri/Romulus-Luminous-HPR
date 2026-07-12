"""Take five photos using Picamera2 (with a safe fallback if unavailable)."""

import time

try:
    from picamera2 import Picamera2
except Exception:
    # Fallback mock for environments without picamera2 installed.
    class Picamera2:
        def start(self):
            print("[mock] Picamera2.start() called")

        def capture_file(self, filename: str):
            # Create a placeholder file to indicate a mock capture.
            with open(filename, "w") as f:
                f.write("This is a placeholder for " + filename + "\n")
            print(f"[mock] captured {filename}")

        def stop(self):
            print("[mock] Picamera2.stop() called")


picam2 = Picamera2()
picam2.start()

time.sleep(2)

for i in range(5):
    filename = f"photo_{i:03d}.jpg"
    picam2.capture_file(filename)

    print(filename)

    time.sleep(0.5)

picam2.stop()