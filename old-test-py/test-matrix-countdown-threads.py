import RPi.GPIO as GPIO
import time
import threading
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.legacy import show_message
from luma.core.legacy.font import proportional, CP437_FONT

# Define GPIO pins for LEDs and button
sequence_pins = [26, 19, 13]
button_pin = 0  # Change this if needed

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for pin in sequence_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Initialize LED matrix
serial = spi(port=0, device=0, gpio=noop())
device = max7219(serial, cascaded=4, block_orientation=-90, rotate=2)

def display_message(msg):
    print(msg)
    show_message(device, msg, fill="white", font=proportional(CP437_FONT), scroll_delay=0.015)

def reset_sequence():
    print("Resetting sequence...")
    for pin in sequence_pins:
        GPIO.output(pin, GPIO.LOW)
    GPIO.output(sequence_pins[0], GPIO.HIGH)

def flash_led():
    last_toggle_time = time.time()
    led_state = False
    while GPIO.input(button_pin) == GPIO.HIGH:
        current_time = time.time()
        if current_time - last_toggle_time >= 0.5:
            led_state = not led_state
            GPIO.output(sequence_pins[1], GPIO.HIGH if led_state else GPIO.LOW)
            last_toggle_time = current_time
        time.sleep(0.01)

def main_loop():
    try:
        while True:
            threading.Thread(target=display_message, args=("Blank noise detected!",)).start()
            
            GPIO.output(sequence_pins[0], GPIO.HIGH)
            print("Flashing second LED, waiting for button press...")
            flash_led_thread = threading.Thread(target=flash_led)
            flash_led_thread.start()
            
            while GPIO.input(button_pin) == GPIO.HIGH:
                time.sleep(0.1)
            
            print("Button pressed! Turning second LED solid and activating third LED.")
            GPIO.output(sequence_pins[1], GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(sequence_pins[2], GPIO.HIGH)
            
            threading.Thread(target=display_message, args=("Firing!",)).start()
            
            click_count = 0
            last_click_time = 0
            while True:
                if GPIO.input(button_pin) == GPIO.LOW:
                    current_time = time.time()
                    if current_time - last_click_time < 0.5:
                        click_count += 1
                    else:
                        click_count = 1
                    last_click_time = current_time
                    while GPIO.input(button_pin) == GPIO.LOW:
                        time.sleep(0.05)
                    if click_count == 2:
                        reset_sequence()
                        break
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        GPIO.cleanup()
        print("GPIO cleanup complete. Exiting program.")

main_loop()