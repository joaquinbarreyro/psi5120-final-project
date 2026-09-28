from gpiozero import Button, LED
from signal import pause

button = Button(17, pull_up=True)

green = LED(27)
red = LED(10)

# Estado inicial: vermelho
green.off()
red.on()

def vehicle_detected():
    print("VEHICLE DETECTED")
    red.off()
    green.on()

def vehicle_left():
    print("VEHICLE LEFT")
    green.off()
    red.on()

button.when_pressed = vehicle_detected
button.when_released = vehicle_left

print("GPIO test running")
print("Press the vehicle detection button...")
pause()
