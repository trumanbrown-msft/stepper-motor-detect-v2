import RPi.GPIO as GPIO
import time

# Define the GPIO pins for the sequence and the button
sequence_pins = [26, 19, 13]  # GPIO pins for the sequence
button_pin = 0  # GPIO pin for the button

# Setup GPIO mode
GPIO.setmode(GPIO.BCM)  # Use BCM numbering

# Set up the GPIO pins for the sequence as output
for pin in sequence_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # Ensure all pins start in LOW state

# Set up the button pin as input with a pull-up resistor
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Turn on the first LED immediately
GPIO.output(sequence_pins[0], GPIO.HIGH)

# Function to flash the second LED until button press
def flash_led():
    while GPIO.input(button_pin) == GPIO.HIGH:
        GPIO.output(sequence_pins[1], GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(sequence_pins[1], GPIO.LOW)
        time.sleep(0.5)

try:
    print("Flashing second LED, waiting for button press...")
    flash_led()  # Start flashing the second LED
    
    print("Button pressed! Turning second LED solid and activating third LED.")
    GPIO.output(sequence_pins[1], GPIO.HIGH)  # Keep second LED on
    time.sleep(0.5)
    GPIO.output(sequence_pins[2], GPIO.HIGH)  # Turn on the third LED

    # Keep the LEDs on
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Program interrupted by user")

finally:
    GPIO.cleanup()
    print("GPIO cleanup complete. Exiting program.")
