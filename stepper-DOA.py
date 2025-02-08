import usb.core
import usb.util
import time
import RPi.GPIO as GPIO
import threading
from tuning import Tuning

# Pin configuration
DIR = 20    
STEP = 21   
CW = 1      
CCW = 0     
SPR = 200    

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

# Initialize ReSpeaker
dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
if not dev:
    raise ValueError("ReSpeaker 4 Mic Array not found")

Mic_tuning = Tuning(dev)

# Shared variable for current motor angle and tracking state
current_angle = 0
tracking = True  # Controls whether the system is tracking sound or calibrating
calibrating = False  # Controls whether the system is in calibration mode

# Function to rotate motor
def rotate_motor(steps, direction):
    GPIO.output(DIR, direction)
    for _ in range(steps):
        GPIO.output(STEP, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(STEP, GPIO.LOW)
        time.sleep(0.001)

# Function to track noise direction and rotate motor
def track_noise():
    global current_angle
    while True:
        if tracking:  # Only track noise if not in calibration mode
            direction = Mic_tuning.direction
            target_angle = (360 - direction) % 360
            angle_diff = target_angle - current_angle

            if angle_diff > 180:
                angle_diff -= 360
            elif angle_diff < -180:
                angle_diff += 360

            move_direction = CW if angle_diff > 0 else CCW
            rotate_motor(abs(int(angle_diff / 1.8)), move_direction)
            current_angle = target_angle

        time.sleep(0.04)

# Function for user calibration with simple control
def calibrate_motor():
    global current_angle, tracking, calibrating
    while True:
        if calibrating:  # Allow calibration only when the system is in calibrating mode
            user_input = input("Press 'a' to rotate counterclockwise, 'd' to rotate clockwise, 'q' to start tracking: ")
            
            if user_input == 'a':
                current_angle -= 1.8  # Rotate counterclockwise by 1.8 degrees
                print(f"Motor rotated to {current_angle} degrees.")
            elif user_input == 'd':
                current_angle += 1.8  # Rotate clockwise by 1.8 degrees
                print(f"Motor rotated to {current_angle} degrees.")
            elif user_input == 'q':
                print("Starting noise tracking.")
                tracking = True  # Resume noise tracking
                calibrating = False  # Exit calibration mode
                break
            else:
                print("Invalid input. Use 'a' to rotate left, 'd' to rotate right, or 'q' to start tracking.")

# Function to begin calibration
def start_calibration():
    global calibrating, tracking
    tracking = False  # Disable tracking during calibration
    calibrating = True  # Enable calibration mode
    print("Calibration mode enabled. Use 'a' or 'd' to manually adjust motor.")
    calibrate_motor()  # Start the calibration

# Start tracking and calibration in parallel
try:
    # Start noise tracking in a separate thread
    track_thread = threading.Thread(target=track_noise, daemon=True)
    track_thread.start()

    # Main thread will allow user to trigger calibration or start tracking
    while True:
        user_input = input("Press 'c' to calibrate the motor, 'q' to start tracking: ")
        
        if user_input == 'c':
            start_calibration()
        elif user_input == 'q':
            print("Starting noise tracking.")
            tracking = True
            calibrating = False
            break
        else:
            print("Invalid input. Press 'c' to calibrate or 'q' to start tracking.")

    # Keep the program running to allow continuous tracking and calibration
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting program.")
    GPIO.cleanup()
