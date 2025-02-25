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
DIR, STEP = 20, 21
CW, CCW = 1, 0
SPR = 200  # Steps per Revolution (1.8° per step)

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

# LED matrix setup
serial = spi(port=0, device=0, gpio=noop())
device = max7219(serial, cascaded=4, block_orientation=-90, rotate=0)

# USB device setup
dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
if not dev:
    raise ValueError("ReSpeaker 4 Mic Array not found")
Mic_tuning = Tuning(dev)

# PyAudio setup
p = pyaudio.PyAudio()
RATE, CHUNK, CHANNELS = 16000, 1024, 6
FORMAT = pyaudio.paInt16
THRESHOLD = 3000

def find_respeaker():
    for i in range(p.get_device_count()):
        if "ReSpeaker" in p.get_device_info_by_index(i)["name"]:
            return i
    raise ValueError("ReSpeaker not found")

stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK, input_device_index=find_respeaker())

# State variables
current_angle, tracking, calibrating = 0, True, False

def calculate_volume(audio_data):
    if not audio_data.any():
        return 0.0
    audio_data = np.clip(np.array(audio_data, dtype=np.int32), -32768, 32767)
    audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=32767, neginf=-32768)
    return np.sqrt(np.mean(np.square(audio_data)))

def led_print(msg):
    print(msg)
    device.clear()
    show_message(device, msg, fill="white", font=proportional(CP437_FONT), scroll_delay=0.01)
    time.sleep(1)
    device.clear()

def audio_processing_thread():
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        if len(data) < CHUNK * CHANNELS * 2:
            continue
        audio_data = np.frombuffer(data, dtype=np.int16).reshape(-1, CHANNELS)[:, 0]
        rms = calculate_volume(audio_data)
        print(f"Volume: {rms:.2f}")
        if rms > THRESHOLD:
            direction = Mic_tuning.direction
            print(f"Loud sound detected! Direction: {direction}°")
            led_print(f"Sound at {direction}°")

def rotate_motor(steps, direction):
    GPIO.output(DIR, direction)
    for _ in range(steps):
        GPIO.output(STEP, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(STEP, GPIO.LOW)
        time.sleep(0.001)

def track_noise():
    global current_angle
    while True:
        if tracking:
            direction = Mic_tuning.direction
            target_angle = (360 - direction) % 360
            angle_diff = (target_angle - current_angle + 180) % 360 - 180
            rotate_motor(abs(int(angle_diff / 1.8)), CW if angle_diff > 0 else CCW)
            current_angle = target_angle
        time.sleep(0.04)

def calibrate_motor():
    global current_angle, tracking, calibrating
    while calibrating:
        user_input = input("'a': counterclockwise, 'd': clockwise, 'q': track: ")
        if user_input == 'a':
            current_angle -= 1.8
            print(f"Motor: {current_angle}°")
        elif user_input == 'd':
            current_angle += 1.8
            print(f"Motor: {current_angle}°")
        elif user_input == 'q':
            tracking, calibrating = True, False
            print("Tracking enabled.")
        else:
            print("Invalid command.")

def start_calibration():
    global tracking, calibrating
    tracking, calibrating = False, True
    print("Calibration mode.")
    calibrate_motor()

try:
    Thread(target=track_noise, daemon=True).start()
    Thread(target=audio_processing_thread, daemon=True).start()

    while True:
        user_input = input("'c': calibrate, 'q': track: ")
        if user_input == 'c':
            start_calibration()
        elif user_input == 'q':
            tracking, calibrating = True, False
            print("Tracking enabled.")
        else:
            print("Invalid command.")
        time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()
    stream.stop_stream()
    stream.close()
    p.terminate()
