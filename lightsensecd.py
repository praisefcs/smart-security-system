import RPi.GPIO as GPIO
import time
from tkinter import Tk, Label, Canvas
from PIL import Image, ImageTk  # Pillow library for image handling

# Pin configuration
PIR_PIN = 17
LED_PINS = [18, 19, 20]
TRIG = 23
ECHO = 24
BUTTON_PIN = 21

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for pin in LED_PINS:
    GPIO.setup(pin, GPIO.OUT)

# Global flags
system_active = False
motion_detected_pir = False
motion_detected_ultrasonic = False

def get_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    pulse_start = time.time()
    pulse_end = time.time()

    timeout = pulse_start + 0.04  # 40ms timeout to avoid lock

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return 999

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return 999

    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * 34300) / 2  # Speed of sound in cm/s
    return round(distance, 2)

def toggle_system(channel):
    global system_active
    system_active = not system_active
    print("System Active" if system_active else "System Down")
    system_status_label.config(text="System: Active" if system_active else "System: Down")

    if not system_active:
        for pin in LED_PINS:
            GPIO.output(pin, False)
        pir_status_label.config(text="PIR Sensor: Off")
        ultrasonic_status_label.config(text="Ultrasonic: Off")

# Event listener for button
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=toggle_system, bouncetime=300)

# GUI update function
def update_gui():
    global motion_detected_pir, motion_detected_ultrasonic

    if system_active:
        distance = get_distance()
        pir_motion = GPIO.input(PIR_PIN)

        # PIR Sensor logic
        if pir_motion and not motion_detected_pir:
            pir_status_label.config(text="Motion detected at front door")
            for pin in LED_PINS:
                GPIO.output(pin, True)
            motion_detected_pir = True
        elif not pir_motion and motion_detected_pir:
            pir_status_label.config(text="Front door: no activity")
            for pin in LED_PINS:
                GPIO.output(pin, False)
            motion_detected_pir = False

        # Ultrasonic logic
        if distance <= 15 and not motion_detected_ultrasonic:
            ultrasonic_status_label.config(text="Someone has entered home")
            motion_detected_ultrasonic = True
        elif distance > 15 and motion_detected_ultrasonic:
            ultrasonic_status_label.config(text="Home empty")
            motion_detected_ultrasonic = False

    root.after(300, update_gui)

# GUI setup
root = Tk()
root.title("LightSense™: Home Monitoring System")
root.geometry("800x600")

# Background image
try:
    background_image = Image.open("/mnt/data/House4project.png")  # Change path if needed
    background_image = background_image.resize((800, 600), Image.ANTIALIAS)
    bg_photo = ImageTk.PhotoImage(background_image)

    canvas = Canvas(root, width=800, height=600)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, anchor="nw", image=bg_photo)
except Exception as e:
    print("Background image failed to load:", e)
    canvas = Canvas(root, width=800, height=600)
    canvas.pack(fill="both", expand=True)

# Labels
system_status_label = Label(root, text="System: Down", font=("Helvetica", 24), bg="white", fg="black")
system_status_label.place(x=50, y=50)

pir_status_label = Label(root, text="PIR Sensor: Off", font=("Helvetica", 24), bg="white", fg="black")
pir_status_label.place(x=50, y=150)

ultrasonic_status_label = Label(root, text="Ultrasonic: Off", font=("Helvetica", 24), bg="white", fg="black")
ultrasonic_status_label.place(x=50, y=250)

# Begin GUI loop
root.after(100, update_gui)

try:
    root.mainloop()
except KeyboardInterrupt:
    print("Exiting program...")
finally:
    GPIO.cleanup()
