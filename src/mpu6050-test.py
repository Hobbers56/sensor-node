import time
import mpu6050
import threading
from datetime import datetime
from gpiozero import LED, DistanceSensor
from picamzero import Camera
from pathlib import Path
import queue

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
IMAGE_DIR = DATA_DIR / "images"
green_led = LED(15)
sensor = DistanceSensor(
    echo=17,
    trigger=4,
    max_distance=4
    )

mpu6050 = mpu6050.mpu6050(0x68)
cam = Camera()
RANGE_HIGH = 5
RANGE_LOW = 3


def read_sensor_data():
    accelerometer_data = mpu6050.get_accel_data()
    
    gyroscope_data = mpu6050.get_gyro_data()
    
    temperature = mpu6050.get_temp()
    
    return accelerometer_data, gyroscope_data, temperature

def get_distance():
    distance = sensor.distance
    return distance

image_queue = queue.Queue(maxsize=3)
def capture_image(image_queue):
    while True:
        try:
            trigger_timestamp, distance = image_queue.get()
            if trigger_timestamp is None:
                break
            image_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"capture_{image_timestamp}.jpg"
            image_path = IMAGE_DIR / filename
            cam.take_photo(image_path)
            print(f"Image captured at {image_timestamp}, distance: {distance:.2f} cm")
        except image_queue.Empty:
            break
    return image_timestamp

capture_thread = threading.Thread(target=capture_image, args=(image_queue,), daemon=True)
capture_thread.start()

previous_in_range = False
while True:
    accelerometer_data, gyroscope_data, temperature = read_sensor_data()
    
    distance = get_distance() * 100
    if distance < 3:
        green_led.on()
    else:
        green_led.off()

    current_in_range = RANGE_LOW < distance < RANGE_HIGH
    
    if current_in_range and not previous_in_range:
        trigger_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        try:
            image_queue.put_nowait((trigger_timestamp, distance))
        except queue.Full:
            print("Image queue is full. Dropping image capture request.")   
        
    previous_in_range = current_in_range
    
    print("Distance: ", distance)
    time.sleep(0.25)
    
    