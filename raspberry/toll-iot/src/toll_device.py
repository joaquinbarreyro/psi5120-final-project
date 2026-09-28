#!/usr/bin/env python3

import subprocess
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path.home() / "toll-iot"
IMAGE_DIR = BASE_DIR / "images"

CAMERA_DEVICE = "/dev/video0"
RESOLUTION = "1280x720"


def capture_image():
    event_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    image_path = IMAGE_DIR / f"{event_id}.jpg"

    print(f"\nEvent ID: {event_id}")
    print("Capturing image...")

    t0_ns = time.monotonic_ns()

    subprocess.run(
        [
            "fswebcam",
            "-q",
            "-d", CAMERA_DEVICE,
            "-r", RESOLUTION,
            "--no-banner",
            str(image_path),
        ],
        check=True,
    )

    t1_ns = time.monotonic_ns()

    capture_ms = (t1_ns - t0_ns) / 1_000_000

    print(f"Image: {image_path}")
    print(f"Capture time: {capture_ms:.2f} ms")

    return event_id, image_path, t0_ns, t1_ns


def main():
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    print("Electronic Toll Collection - Roadside Device")
    print(f"Camera: {CAMERA_DEVICE}")
    print(f"Resolution: {RESOLUTION}")
    print("Press ENTER to simulate vehicle detection.")
    print("Ctrl+C to exit.")

    try:
        while True:
            input("\nWaiting for vehicle... ")
            capture_image()

    except KeyboardInterrupt:
        print("\nFinished.")


if __name__ == "__main__":
    main()
