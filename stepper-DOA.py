import usb.core
import usb.util
import time
import RPi.GPIO as GPIO
import numpy as np
from tuning import Tuning
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop


# Pin configuration
DIR = 20    # Direction GPIO Pin
STEP = 21   # Step GPIO Pin
CW = 1      # Clockwise Rotation
CCW = 0     # Counterclockwise Rotation
SPR = 200   # Steps per Revolution (1.8° per step)

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

# Setup LED matrix
serial = spi(port=0, device=0, gpio=noop())
device = max7219(serial, cascaded=4, block_orientation=-90, rotate=0, blocks_arranged_in_reverse_order=False)
print("Created LED Matrix device")

# Initialize USB device for ReSpeaker
dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)

if not dev:
    raise ValueError("ReSpeaker 4 Mic Array not found")

Mic_tuning = Tuning(dev)

# Track audio direction and point motor
try:
    current_angle = 0  # Track the motor's position
    while True:
        direction = Mic_tuning.direction
        print(f"Audio direction: {direction} degrees")

        # Calculate target angle based on direction
        target_angle = 360 - direction  # Flip direction
        # Normalize the target angle to within 0-360 degrees
        target_angle = target_angle % 360

        # Calculate the difference in angles
        angle_diff = target_angle - current_angle

        # Ensure angle_diff is between -180 and 180 (shortest path)
        if angle_diff > 180:
            angle_diff -= 360
        elif angle_diff < -180:
            angle_diff += 360

        # Determine rotation direction (shortest path)
        if angle_diff > 0:
            GPIO.output(DIR, CW)  # Clockwise
        else:
            GPIO.output(DIR, CCW)  # Counterclockwise

        # Rotate stepper motor (non-blocking)
        step_count = int(abs(angle_diff) / 1.8)  # Steps per revolution (1.8° per step)
        for _ in range(step_count):
            GPIO.output(STEP, GPIO.HIGH)
            time.sleep(0.001)
            GPIO.output(STEP, GPIO.LOW)
            time.sleep(0.001)

        # Update current angle
        current_angle = target_angle

        # Small delay to prevent rapid movement
        time.sleep(0.04)

except KeyboardInterrupt:
    print("Exiting program.")
    GPIO.cleanup()