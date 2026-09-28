from gpiozero import Button
from signal import pause
from datetime import datetime

button = Button(17, pull_up=True, bounce_time=0.05)

def vehicle_detected():
    print(
        f"Vehicle detected: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}"
    )

button.when_pressed = vehicle_detected

print("Waiting for button...")
print("Ctrl+C to exit.")

pause()
