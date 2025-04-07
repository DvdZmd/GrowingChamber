import struct
from flask import Flask, request, jsonify, Response, render_template
from picamera2 import Picamera2
from flask_cors import CORS
import cv2
import threading
import smbus2  # I²C communication
import time 
from smbus2 import i2c_msg


# Flask app setup
app = Flask(__name__)
CORS(app)

# Initialize the camera
picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={"size": (2000, 2000)},
    controls={"FrameRate": 60, "NoiseReductionMode": 2}
)
picam2.configure(video_config)
picam2.start()


i2c_lock = threading.Lock()

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


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


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
