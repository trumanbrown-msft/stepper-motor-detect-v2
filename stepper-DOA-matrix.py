import usb.core
import usb.util
import time
import RPi.GPIO as GPIO
import numpy as np
import pyaudio
from threading import Thread
from tuning import Tuning
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.legacy import show_message
from luma.core.legacy.font import proportional, CP437_FONT

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

# Set up PyAudio for real-time audio capture
p = pyaudio.PyAudio()

# Parameters for audio capture
rate = 16000  # Sample rate for ReSpeaker 4-Mic Array
chunk = 24000  # Chunk size (1.5 seconds)
overlap = 18000  # 75% overlap (1.125 seconds overlap)
channels = 1  # Mono audio
format = pyaudio.paInt16
THRESHOLD = 30 # Volume threshold for noise detection

# Open the audio stream
stream = p.open(format=format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=chunk)

# Shared variable for current motor angle and tracking state
current_angle = 0
tracking = True  # Controls whether the system is tracking sound or calibrating
calibrating = False  # Controls whether the system is in calibration mode

# Function to calculate volume from raw audio data
def calculate_volume(data):
    try:
        # Ensure data is in the expected format
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        if len(audio_data) == 0:
            raise ValueError("Audio data is empty.")

        # Root mean square (RMS) method for volume
        volume = np.sqrt(np.mean(audio_data**2))

        # Prevent invalid values from being returned
        if np.isnan(volume) or volume < 0:
            return 0.0

        return volume
    except Exception as e:
        print(f"Error calculating volume: {e}")
        return 0.0

# Function to show the message on the LED matrix
def led_print(msg):
    print(msg)
    device.clear()  # Clear the screen before showing the message
    show_message(device, msg, fill="white", font=proportional(CP437_FONT), scroll_delay=0.01)  # No scrolling
    # Wait for a short time before clearing the message (e.g., 1 second)
    time.sleep(1)
    device.clear()  # Clear the screen after the message is displayed

# Function to detect loud audio and trigger message display
def audio_processing_thread():
    while True:
        audio_data = stream.read(chunk, exception_on_overflow=False)
        volume = calculate_volume(audio_data)

        # Check if the noise is loud enough to trigger a message
        if volume > THRESHOLD:
            led_print("Noise!")

        time.sleep(0.1)  # Small delay to prevent overloading the CPU

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
    track_thread = Thread(target=track_noise, daemon=True)
    track_thread.start()

    # Start the audio processing thread
    audio_thread = Thread(target=audio_processing_thread, daemon=True)
    audio_thread.start()

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
    stream.stop_stream()
    stream.close()
    p.terminate()
