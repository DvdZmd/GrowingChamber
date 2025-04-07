import os
import struct
import subprocess
import threading
import time
from datetime import datetime

from flask import Flask, request, jsonify, Response, render_template, send_file
from flask_cors import CORS

import cv2
from threading import Thread, Event

# I²C communication
import smbus2  
from smbus2 import i2c_msg

from picamera2 import Picamera2


# Flask app setup
app = Flask(__name__)
CORS(app)

timelapse_thread = None
timelapse_stop_event = Event()

i2c_lock = threading.Lock()


# Initialize the camera
AVAILABLE_RESOLUTIONS = [
    (640, 480),     # VGA
    (800, 600),     # SVGA
    (1280, 720),    # HD 720p
    (1920, 1080),   # Full HD
    (2592, 1944),   # Max resolution for Pi Cam v1.3 (5MP)
]

picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={"size": (2000, 2000)},
    controls={"FrameRate": 60, "NoiseReductionMode": 2}
)
picam2.configure(video_config)
picam2.start()



# I²C Addresses
ARDUINO_PAN_TILT = 0x10  # Arduino controlling the servos
ARDUINO_SENSORS = 0x20    # Arduino reading sensors

# I²C Bus
bus = smbus2.SMBus(1)  # Use I²C bus 1 (default for Raspberry Pi)

# Sensor Data
sensor_data = {
    "temperature_dht": 0.0,
    "humidity": 0.0,
    "temperature_ds18b20": 0.0,
    "soil_moisture": 0
}

servo_position = {
    "pan": 90,
    "tilt": 90
}

requested_pan = None
requested_tilt = None

# ======= CAMERA STREAM FUNCTION ===========
def generate_frames():
    while True:
        frame = picam2.capture_array()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rotated = cv2.rotate(frame_rgb, cv2.ROTATE_180)
        _, buffer = cv2.imencode('.jpg', frame_rotated)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def timelapse_worker(interval_minutes, width, height):
    global picam2, video_config

    while not timelapse_stop_event.is_set():
        try:
            resolution = (width, height)

            if resolution not in AVAILABLE_RESOLUTIONS:
                print(f"[Timelapse] Unsupported resolution: {resolution}")
                break

            # Reconfigure for still capture
            picam2.stop()
            still_config = picam2.create_still_configuration(main={"size": resolution})
            picam2.configure(still_config)
            picam2.start()
            time.sleep(0.5)


            image = picam2.capture_array()
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


            # Create timelapse folder structure
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            timelapse_dir = os.path.join(root_dir, "Pictures", "Timelapse")
            date_folder = datetime.now().strftime("%Y-%m-%d")
            save_folder = os.path.join(timelapse_dir, date_folder)
            os.makedirs(save_folder, exist_ok=True)

            timestamp = datetime.now().strftime("%H-%M-%S")
            filename = f"{timestamp}.jpg"
            filepath = os.path.join(save_folder, filename)

            cv2.imwrite(filepath, image)
            print(f"[Timelapse] Saved: {filepath}")

        except Exception as e:
            print(f"[Timelapse Error] {e}")

        finally:
            # Restore video stream
            try:
                picam2.stop()
                picam2.configure(video_config)
                picam2.start()
            except Exception as e:
                print(f"[Timelapse Restore Error] {e}")

        # Wait for the next interval or exit early
        if timelapse_stop_event.wait(interval_minutes * 60):
            break

    print("[Timelapse] Stopped")


@app.route('/timelapse', methods=['POST'])
def handle_timelapse():
    global timelapse_thread, timelapse_stop_event

    data = request.get_json()
    action = data.get("action")

    if action == "start":
        if timelapse_thread and timelapse_thread.is_alive():
            return jsonify({"message": "Timelapse already running"}), 400

        interval = int(data.get("interval_minutes", 5))
        width = int(data.get("width", 640))
        height = int(data.get("height", 480))

        timelapse_stop_event.clear()
        timelapse_thread = Thread(target=timelapse_worker, args=(interval, width, height))
        timelapse_thread.start()

        return jsonify({"message": f"✅ Timelapse started every {interval} min at {width}x{height}"}), 200

    elif action == "stop":
        if timelapse_thread and timelapse_thread.is_alive():
            timelapse_stop_event.set()
            timelapse_thread.join()
            return jsonify({"message": "🛑 Timelapse stopped"}), 200
        else:
            return jsonify({"message": "Timelapse is not running"}), 400

    return jsonify({"message": "Invalid action"}), 400



@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_image', methods=['GET'])
def capture_image():
    try:
        width = int(request.args.get("width", 640))
        height = int(request.args.get("height", 480))
        resolution = (width, height)

        if resolution not in AVAILABLE_RESOLUTIONS:
            return jsonify({
                "error": "Unsupported resolution",
                "available_resolutions": AVAILABLE_RESOLUTIONS
            }), 400

        # Stop current stream, reconfigure for still capture
        picam2.stop()
        still_config = picam2.create_still_configuration(main={"size": resolution})
        picam2.configure(still_config)
        picam2.start()
        time.sleep(0.5)

        # Capture image
        image = picam2.capture_array()
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Prepare folder structure
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # Go up from /Server
        pictures_dir = os.path.join(root_dir, "Pictures")
        date_folder = datetime.now().strftime("%Y-%m-%d")
        save_folder = os.path.join(pictures_dir, date_folder)
        os.makedirs(save_folder, exist_ok=True)

        # Create filename with current time
        timestamp = datetime.now().strftime("%H-%M-%S")
        filename = f"{timestamp}.jpg"
        filepath = os.path.join(save_folder, filename)

        cv2.imwrite(filepath, image)

        # Restore video config
        picam2.stop()
        picam2.configure(video_config)
        picam2.start()

        # Return the file
        return send_file(filepath, mimetype='image/jpeg', as_attachment=True)

    except Exception as e:
        return jsonify({"error": f"Failed to capture image: {e}"}), 500


# ======= SERVO CONTROL FUNCTION ===========
@app.route('/request_current_pan_tilt', methods=['GET'])
def request_current_pan_tilt():
    with i2c_lock:
        #=== 2. Get current servo angles ===
        try:
            time.sleep(0.01)  # Small delay before reading
            read = i2c_msg.read(ARDUINO_PAN_TILT, 2)
            bus.i2c_rdwr(read)
            data = list(read)
            servo_position = {
                "pan": data[0],
                "tilt": data[1]
            } 
        except Exception as e:
            print(f"[I2C ERROR] Failed to read servo angles: {e}")
            servo_position = {
                "pan": 0,
                "tilt": 0
            }

    return jsonify(servo_position)

@app.route('/send_pan_tilt', methods=['POST'])
def send_pan_tilt():
    global requested_pan, requested_tilt, servo_position
    data = request.get_json()
    if 'pan' in data and 'tilt' in data:
        requested_pan = max(90, min(160, int(data['pan'])))
        requested_tilt = max(0, min(180, int(data['tilt'])))

        try:
            with i2c_lock:
                bus.write_i2c_block_data(ARDUINO_PAN_TILT, 0x00, [requested_pan, requested_tilt])
            time.sleep(0.03)

            servo_position = {
                "pan": requested_pan,
                "tilt": requested_tilt
            }
        except Exception as e:
            print(f"[I2C ERROR] Failed to send servo command: {e}")
            print(f"Requested pan: {requested_pan}, Requested tilt: {requested_tilt}")
            servo_position = {
                "pan": 0,
                "tilt": 0
            }

        return jsonify({
            "message": "Servo command queued",
            "requested_pan": requested_pan,
            "requested_tilt": requested_tilt
        })
    
    else:
        return jsonify({"error": "Missing pan or tilt value"}), 400


# ======= READ SENSOR DATA FROM ARDUINO ===========
@app.route('/get_sensors', methods=['GET'])
def get_sensors():
    try:
        with i2c_lock:
            raw_data_list = bus.read_i2c_block_data(ARDUINO_SENSORS, 0, 14)
        time.sleep(0.03)
        raw_data = bytes(raw_data_list)
        temperature_dht, humidity, temperature_ds18b20, soil_moisture = struct.unpack('<fffH', raw_data)
        sensor_data = {
            "temperature_dht": temperature_dht,
            "humidity": humidity,
            "temperature_ds18b20": temperature_ds18b20,
            "soil_moisture": soil_moisture
        }
    except Exception as e:
        print(f"[I2C ERROR] Failed to read sensor data: {e}")
        sensor_data = {
            "temperature_dht": 0.0,
            "humidity": 0.0,
            "temperature_ds18b20": 0.0,
            "soil_moisture": 0
        }

    return jsonify({
        "temperature_dht": round(sensor_data["temperature_dht"], 2),
        "humidity": round(sensor_data["humidity"], 2),
        "temperature_ds18b20": round(sensor_data["temperature_ds18b20"], 2),
        "soil_moisture": sensor_data["soil_moisture"]
    })


# ======= RUN FLASK SERVER ===========
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
