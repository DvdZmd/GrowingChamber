# GrowingChamber

GrowingChamber is a professional monitoring and control system for mushroom or plant crops. It leverages a Raspberry Pi running a Python REST web server to provide real-time video streaming, environmental monitoring, automated image capture, and I²C-based actuator/sensor communication.

## Features

- **Live Video Streaming:** Stream real-time video from the Raspberry Pi camera via web interface.
- **Environmental Monitoring:** View current air/substrate temperature, humidity, and soil moisture.
- **Pan & Tilt Camera Control:** Remotely control the camera's pan and tilt via servos.
- **Timelapse Photography (Configurable):**
  - Start/stop timelapse from the UI.
  - Set custom resolution and capture interval (e.g., every 1 min).
  - Configuration is **persisted in the database**.
  - Timelapse runs in the background even after UI/browser closes.
- **Automatic Sensor Logging:**
  - Sensor readings are automatically saved at intervals (e.g., every 1 min) using a background logger.
  - Interval is configurable in `config.py`.
- **Sensor Readings History:**
  - Paginated, filterable history of all sensor data (via REST API and UI).
  - Filter by date and value ranges (temperature, humidity, moisture).
- **Resolution Control:** Dynamically switch resolution of live stream and still images.
- **Smart Plug Control:** Control Tuya-compatible smart plugs (e.g., lights, humidifiers).
- **I²C Communication:**
  - Raspberry Pi communicates with two ATmega microcontrollers over I²C:
    - One for pan & tilt servo control.
    - One for environmental sensor readings.

## System Architecture

- **Raspberry Pi:** Hosts the Flask API, handles camera logic, and stores captured images/data.
- **ATmega Microcontrollers:**
  - **Pan/Tilt Controller:** Receives pan/tilt commands via I²C.
  - **Sensor Node:** Continuously reads from sensors and responds to I²C read requests.
- **Web Interface:**
  - HTML/JS frontend.
  - Modular structure using JS modules (`servoControl.js`, `timelapse.js`, etc.)
  - Auto-syncs with backend state on load (e.g., timelapse running or not).
- **Persistence:**
  - Uses SQLite (`app.db`) to store sensor data, timelapse configuration, and user data.
  - Timelapse settings survive reboots.

## Getting Started

### Prerequisites

- Raspberry Pi (Pi 4 or newer)
- Picamera2-compatible camera
- Two ATmega microcontrollers (e.g., Arduino Uno/Nano)
- Sensors: DHT22 (air temp/humidity), DS18B20 (substrate temp), soil moisture
- Pan & tilt servo hardware
- Tuya-based smart plug (optional)
- I²C wiring between Pi and ATmegas

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/GrowingChamber.git
   cd GrowingChamber
   ```

2. **Run the Setup Script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Flash the Microcontrollers**
   - `Arduino/PanTilt/PanTilt.ino` → pan/tilt ATmega
   - `Arduino/SensorsReadings/SensorsReadings.ino` → sensor ATmega

4. **Start the Server**
   ```bash
   source .venv/bin/activate
   python Server/app.py
   ```
   Web interface will be available at: [http://localhost:5000](http://localhost:5000)

### Configuration

Edit `Server/config.py` to adjust:
- Camera resolution, frame rate, noise settings
- I²C device addresses
- Smart plug IP/device ID/key
- Sensor logging interval (`SENSOR_LOG_INTERVAL = '1m'`)
- Timelapse directory (`TIMELAPSE_DIR = '/your/path'`)
- Enable/disable features (e.g., `ENABLE_SENSOR_LOGGER = True`)

## Usage Highlights

### 🔹 Sensor Logging

Sensor data is automatically logged in the background at intervals (e.g., every 1 minute). You can adjust this via:

```python
# config.py
SENSOR_LOG_INTERVAL = '1m'  # 10s, 30s, 5m, 1h, etc.
```

### 🔹 Timelapse System

- Start/stop timelapse from the web UI.
- Set custom resolution + interval.
- All settings are persisted in the database (even after reboot).
- Use `/timelapse_status` to get current status + settings.

### 🔹 History API (Sensor Readings)

`GET /readings_history` supports:
- Pagination (`page`, `per_page`)
- Filters:
  - `start_date`, `end_date` (YYYY-MM-DD)
  - `min_temp_air`, `max_temp_air`
  - `min_humidity`, `max_humidity`
  - `min_temp_sub`, `max_temp_sub`
  - `min_moisture`, `max_moisture`

## Folder Structure (Simplified)

```
Server/
├── app.py
├── config.py
├── camera/
│   ├── picam.py           # Picamera2 init/config
│   ├── timelapse.py       # Background timelapse logic
├── database/
│   ├── models.py          # SQLAlchemy models
│   └── app.db             # SQLite database
├── routes/
│   ├── camera_routes.py
│   ├── i2c_routes.py
│   └── smartplug_routes.py
├── sensors_logger/
│   └── sensor_logger.py   # Background sensor logging loop
├── static/
│   ├── main.js
│   ├── timelapse.js
│   └── ...
├── templates/
│   └── index.html
```

## License

MIT License. See [LICENSE](LICENSE).

## Acknowledgments

- [Picamera2](https://github.com/raspberrypi/picamera2)
- [Flask](https://flask.palletsprojects.com/)
- [TinyTuya](https://github.com/jasonacox/tinytuya)
- [OpenCV](https://opencv.org/)


---

For further details, refer to the source code and comments in each module.