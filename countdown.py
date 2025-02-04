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

# Function to reset the sequence
def reset_sequence():
    print("Resetting sequence...")
    for pin in sequence_pins:
        GPIO.output(pin, GPIO.LOW)
    GPIO.output(sequence_pins[0], GPIO.HIGH)  # Restart first LED

def flash_led():
    """Flashes the second LED while checking for button press in real-time."""
    last_toggle_time = time.time()
    led_state = False  # Track LED state

    while GPIO.input(button_pin) == GPIO.HIGH:
        current_time = time.time()
        
        # Toggle LED every 0.5 seconds
        if current_time - last_toggle_time >= 0.5:
            led_state = not led_state  # Flip LED state
            GPIO.output(sequence_pins[1], GPIO.HIGH if led_state else GPIO.LOW)
            last_toggle_time = current_time

        time.sleep(0.01)  # Small delay to reduce CPU usage

# Main loop
try:
    while True:
        # Initial state: First LED on
        GPIO.output(sequence_pins[0], GPIO.HIGH)
        print("Flashing second LED, waiting for button press...")
        
        # Flash second LED until button is pressed
        flash_led()

        # Button pressed: Activate second LED permanently
        print("Button pressed! Turning second LED solid and activating third LED.")
        GPIO.output(sequence_pins[1], GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(sequence_pins[2], GPIO.HIGH)

        # Wait for user input (single or double click detection)
        click_count = 0
        last_click_time = 0

        while True:
            if GPIO.input(button_pin) == GPIO.LOW:  # Button pressed
                current_time = time.time()
                
                # Check if it's a double click (within 500ms)
                if current_time - last_click_time < 0.5:
                    click_count += 1
                else:
                    click_count = 1  # Reset click count if too slow

                last_click_time = current_time

                while GPIO.input(button_pin) == GPIO.LOW:  # Wait for release
                    time.sleep(0.05)

                if click_count == 2:  # Double click detected
                    reset_sequence()
                    break  # Restart main loop
        
            time.sleep(0.1)  # Small delay to avoid excessive CPU usage

except KeyboardInterrupt:
    print("Program interrupted by user")

finally:
    GPIO.cleanup()
    print("GPIO cleanup complete. Exiting program.")
