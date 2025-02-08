import RPi.GPIO as GPIO
from time import sleep

# Pin configuration
DIR = 20    # Direction GPIO Pin
STEP = 21   # Step GPIO Pin
CW = 1      # Clockwise Rotation
CCW = 0     # Counterclockwise Rotation
SPR = 200   # Steps per Revolution

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

# Start settings
delay = 0.0004  # Minimum delay for max speed
direction = CW  # Start rotating clockwise

try:
    while True:
        GPIO.output(DIR, direction)
        for _ in range(SPR):
            GPIO.output(STEP, GPIO.HIGH)
            sleep(delay)
            GPIO.output(STEP, GPIO.LOW)
            sleep(delay)

        # # Reverse direction after each full revolution
        # direction = CW if direction == CCW else CCW

except KeyboardInterrupt:
    GPIO.cleanup()
    print("Motor stopped and GPIO cleaned up.")
