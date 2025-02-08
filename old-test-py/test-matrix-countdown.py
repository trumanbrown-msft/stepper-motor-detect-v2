import RPi.GPIO as GPIO
import time
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.legacy import show_message
from luma.core.legacy.font import proportional, CP437_FONT

# GPIO setup
sequence_pins = [26, 19, 13]  # GPIO pins for LEDs
button_pin = 0  # GPIO pin for the button

GPIO.setmode(GPIO.BCM)
for pin in sequence_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# LED Matrix setup
serial = spi(port=0, device=0, gpio=noop())
device = max7219(serial, cascaded=4, block_orientation=-90, rotate=2)

# Function to reset LED sequence
def reset_sequence():
    print("Resetting sequence...")
    for pin in sequence_pins:
        GPIO.output(pin, GPIO.LOW)
    GPIO.output(sequence_pins[0], GPIO.HIGH)

# Function to display message on the LED matrix
def display_message(msg):
    show_message(device, msg, fill="white", font=proportional(CP437_FONT), scroll_delay=0.05)

# Main loop
try:
    GPIO.output(sequence_pins[0], GPIO.HIGH)  # Start first LED on
    while True:
        click_count = 0
        last_click_time = 0

        while True:
            if GPIO.input(button_pin) == GPIO.LOW:  # Button pressed
                current_time = time.time()

                if current_time - last_click_time < 0.5:
                    click_count += 1
                else:
                    click_count = 1

                last_click_time = current_time

                while GPIO.input(button_pin) == GPIO.LOW:
                    time.sleep(0.05)

                if click_count == 2:  # Double click → Reset sequence
                    display_message("Test new")
                    reset_sequence()
                    break

                elif click_count == 1:  # Single click → Fire!
                    display_message("Fire!")
                    GPIO.output(sequence_pins[1], GPIO.HIGH)
                    time.sleep(0.5)
                    GPIO.output(sequence_pins[2], GPIO.HIGH)
                    break

            time.sleep(0.1)

except KeyboardInterrupt:
    print("Program interrupted by user")

finally:
    GPIO.cleanup()
    print("GPIO cleanup complete. Exiting program.")
