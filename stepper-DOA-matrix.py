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
device = max7219(spi(port=0, device=0, gpio=noop()), cascaded=4, block_orientation=-90, rotate=0)

# USB device initialization
dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
if not dev:
    raise ValueError("ReSpeaker 4 Mic Array not found")
Mic_tuning = Tuning(dev)

# Audio setup
p = pyaudio.PyAudio()
RATE, CHUNK, CHANNELS, FORMAT, THRESHOLD = 16000, 1024, 6, pyaudio.paInt16, 3000

def find_respeaker():
    for i in range(p.get_device_count()):
        if "ReSpeaker" in p.get_device_info_by_index(i)["name"]:
            return i
    raise ValueError("ReSpeaker not found")

device_index = find_respeaker()
stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK, input_device_index=device_index)

# State variables
current_angle, tracking, calibrating = 0, True, False

def calculate_volume(audio_data):
    audio_data = np.clip(np.array(audio_data, dtype=np.int32), -32768, 32767)
    return np.sqrt(np.mean(np.square(np.nan_to_num(audio_data))))

def led_print(msg):
    device.clear()
    show_message(device, msg, fill="white", font=proportional(CP437_FONT), scroll_delay=0.01)
    time.sleep(1)
    device.clear()

def audio_processing_thread():
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16).reshape(-1, CHANNELS)[:, 0]
        rms = calculate_volume(audio_data)
        if rms > THRESHOLD:
            led_print(f"Sound at {Mic_tuning.direction}°")

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
            target_angle = (360 - Mic_tuning.direction) % 360
            angle_diff = (target_angle - current_angle + 180) % 360 - 180
            rotate_motor(abs(int(angle_diff / 1.8)), CW if angle_diff > 0 else CCW)
            current_angle = target_angle
        time.sleep(0.04)

def calibrate_motor():
    global current_angle, tracking, calibrating
    while calibrating:
        cmd = input("'a': CCW, 'd': CW, 'q': start tracking: ")
        if cmd == 'a':
            current_angle -= 1.8
        elif cmd == 'd':
            current_angle += 1.8
        elif cmd == 'q':
            tracking, calibrating = True, False
            break

def start_calibration():
    global calibrating, tracking
    tracking, calibrating = False, True
    calibrate_motor()

try:
    Thread(target=track_noise, daemon=True).start()
    Thread(target=audio_processing_thread, daemon=True).start()

    while True:
        cmd = input("'c': calibrate, 'q': track: ")
        if cmd == 'c':
            start_calibration()
        elif cmd == 'q':
            tracking, calibrating = True, False
        else:
            print("Invalid command")

except KeyboardInterrupt:
    GPIO.cleanup()
    stream.stop_stream()
    stream.close()
    p.terminate()