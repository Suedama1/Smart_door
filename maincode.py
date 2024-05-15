import RPi.GPIO as GPIO
from time import sleep
import requests
from picamera import PiCamera
import os
import threading

# Telegram Bot Info
# TOKEN = 'YOUR TOKEN'
TOKEN='1234567890:ABCDEfghijKLMNopqrSTUvwxYZ1234567890'
# chat_id = 'YOUR CHAT ID'
chat_id = "987654321"

# Set up GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Motion sensor
GPIO.setup(17, GPIO.IN)

# Keypad
MATRIX = [['1', '2', '3'],
          ['4', '5', '6'],
          ['7', '8', '9'],
          ['*', '0', '#']]
ROW = [6, 20, 19, 13]
COL = [12, 5, 16]

# Slider servo
GPIO.setup(26, GPIO.OUT)
pwm = GPIO.PWM(26, 50)

# Buzzer 
GPIO.setup(18, GPIO.OUT)
GPIO.output(18, 0)

# LED
GPIO.setup(27, GPIO.OUT)
GPIO.output(27, 0)

# Camera setup
camera = PiCamera()

def check_password():
    for i in range(3):
        GPIO.setup(COL[i], GPIO.OUT, initial=GPIO.HIGH)
    for j in range(4):
        GPIO.setup(ROW[j], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    password = ""
    key_pressed = False 
    while len(password) < 4:
        for i in range(3):
            GPIO.output(COL[i], 0)
            for j in range(4):
                if GPIO.input(ROW[j]) == 0:
                    if not key_pressed:
                        key_press = MATRIX[j][i]
                        print(f"Key pressed: {key_press}")
                        password += key_press
                        key_pressed = True  # Set the flag to True
                        sleep(0.2)  # idk if there's no sleep the keypad detects input multiple times
                else:
                    key_pressed = False
            GPIO.output(COL[i], 1)
    return password

def activate_slider(open_time=4):
    GPIO.output(27, 1)
    pwm.start(3)
    sleep(open_time)
    pwm.start(12)
    sleep(open_time)
    GPIO.output(27, 0)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {'chat_id': chat_id, 'text': message}
    response = requests.post(url, data=data)
    print(response.json())

def send_image_via_telegram(image_path):
    """Sends an image file via Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as image_file:
        files = {'photo': (image_path, image_file)}
        data = {'chat_id': chat_id}
        response = requests.post(url, files=files, data=data)
        print(response.json())

def capture_and_send_image():
    try:
        camera.capture('/home/pi/Desktop/image.jpg')
        print("Image captured and saved")
        send_image_via_telegram('/home/pi/Desktop/image.jpg')
    except Exception as err:
        print(f"An error occurred while capturing the image: {err}")


def motion_detected():
    if GPIO.input(17) == 0:
        print("Motion detected")
        capture_and_send_image()
        print("Image captured and sent")
        # Add sleep to prevent perma motion detected
        sleep(5)
        return True
    return False

def motion_detection_loop():
    while True:
        motion_detected()  # This will automatically handle motion detection and image capture
        sleep(0.1)  # Adjust as needed, though your motion_detected function already includes a sleep

def password_check_loop():
    while True:
        password = check_password()
        if password == "1234":
            print("Correct password")
            activate_slider()
            send_telegram_message("Door unlocked successfully.")
        else:
            print("Incorrect password")
            send_telegram_message("Alert: Incorrect password attempt.")
            capture_and_send_image()
            print("Image captured and sent")
            # Buzzer buzz when incorrect password
            light_led()
            ring_buzzer()
            sleep(0.5)
            GPIO.output(18, 0)
        sleep(0.1)  # Prevent this loop from hogging the CPU

def light_led():
    GPIO.output(27, 1)
    sleep(3)
    GPIO.output(27, 0)

def ring_buzzer():
    GPIO.output(18, 1)
    sleep(0.5)
    GPIO.output(18, 0)

def main():
    motion_thread = threading.Thread(target=motion_detection_loop)
    keypad_thread = threading.Thread(target=password_check_loop)

    motion_thread.start()
    keypad_thread.start()

    try:
        motion_thread.join()
        keypad_thread.join()
    except KeyboardInterrupt:
        print("Program stopped by user.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    try:
        camera.start_preview()
        main()
    except KeyboardInterrupt:
        print("Program stopped by user.")
    finally:
        camera.stop_preview()
        camera.close()
        GPIO.cleanup()
