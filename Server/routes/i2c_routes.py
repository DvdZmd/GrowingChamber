import struct
import threading
import time
from flask import Blueprint, request, jsonify
from smbus2 import i2c_msg
import smbus2
import config
from config import ARDUINO_PAN_TILT, ARDUINO_SENSORS, READ_SENSORS, READ_SERVOS, READ_SENSORS_INTERVAL, READ_SERVOS_INTERVAL
# from i2c.sensors import send_sensor_data, request_sensor_data
# from i2c.servos import send_pan_tilt, request_pan_tilt
# from i2c.sensors import read_sensor_data

i2c_lock = threading.Lock()

# I²C Bus
bus = smbus2.SMBus(1)  # Use I²C bus 1 (default for Raspberry Pi)
i2c_bp = Blueprint('i2c', __name__)


# ======= SERVO CONTROL FUNCTION ===========
@i2c_bp.route('/request_current_pan_tilt', methods=['GET'])
def request_current_pan_tilt():
    
    if not READ_SERVOS:
        return jsonify({"error": "Servo control is disabled"}), 503

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

@i2c_bp.route('/send_pan_tilt', methods=['POST'])
def send_pan_tilt():
    global requested_pan, requested_tilt, servo_position

    if not READ_SERVOS:
        return jsonify({"error": "Servo control is disabled"}), 503

    data = request.get_json()
    if 'pan' in data and 'tilt' in data:
        requested_pan = max(90, min(160, int(data['pan'])))
        requested_tilt = max(0, min(180, int(data['tilt'])))

        try:
            with i2c_lock:
                bus.write_i2c_block_data(ARDUINO_PAN_TILT, 0x00, [requested_pan, requested_tilt])
            time.sleep(READ_SERVOS_INTERVAL)  # Small delay before reading
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
@i2c_bp.route('/get_sensors', methods=['GET'])
def get_sensors():
    try:
        if not READ_SENSORS:
            return jsonify({"error": "Sensor reading is disabled"}), 503
        
        #=== 1. Read sensor data ===
        with i2c_lock:
            raw_data_list = bus.read_i2c_block_data(ARDUINO_SENSORS, 0, 14)
        time.sleep(READ_SENSORS_INTERVAL)  # Small delay before reading 

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