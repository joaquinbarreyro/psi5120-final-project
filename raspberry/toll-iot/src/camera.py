import subprocess
import time
from datetime import datetime
from pathlib import Path


class Camera:

    def __init__(
        self,
        image_dir,
        device="/dev/video0",
        resolution="1280x720"
    ):
        self.image_dir = Path(image_dir)
        self.device = device
        self.resolution = resolution

        self.image_dir.mkdir(parents=True, exist_ok=True)


    def capturaFoto(self):

        event_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        image_path = self.image_dir / f"{event_id}.jpg"

        print(f"Event ID: {event_id}")
        print("Capturing image...")

        t0_ns = time.monotonic_ns()

        subprocess.run(
            [
                "fswebcam",
                "-q",
                "-d", self.device,
                "-r", self.resolution,
                "--no-banner",
                str(image_path),
            ],
            check=True,
        )

        t1_ns = time.monotonic_ns()

        capture_ms = (t1_ns - t0_ns) / 1_000_000

        print(f"Image: {image_path}")
        print(f"Capture time: {capture_ms:.2f} ms")

        return event_id, image_path
