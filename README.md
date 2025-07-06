# SmartFungi

SmartFungi is a professional monitoring and control system for mushroom or plant crops. It leverages a Raspberry Pi running a Python REST web server to provide real-time video streaming, environmental monitoring, and automated camera control. The system is designed for research, agricultural automation, and precision crop management.

## Features

- **Live Video Streaming:** Stream real-time video from the Raspberry Pi camera module via a web interface.
- **Environmental Monitoring:** View current environmental conditions, including air and substrate temperature, humidity, and soil moisture.
- **Pan & Tilt Camera Control:** Remotely control camera orientation (pan and tilt) via the web interface.
- **Timelapse Photography:** Schedule periodic image captures for timelapse analysis.
- **Resolution Control:** Dynamically change video and image capture resolutions.
- **I²C Communication:** The Raspberry Pi communicates with two ATmega microcontrollers over I²C:
  - One for pan & tilt servo control.
  - One for sensor data acquisition.

## System Architecture

- **Raspberry Pi:** Hosts the Flask-based REST API and serves the web interface.
- **ATmega Microcontrollers:**
  - **Pan/Tilt Controller:** Receives commands to adjust camera orientation.
  - **Sensor Node:** Reads environmental sensors (DHT22, DS18B20, soil moisture) and provides data to the Pi.
- **Web Interface:** HTML/JavaScript frontend for live monitoring and control.

## Getting Started

### Prerequisites

- Raspberry Pi (recommended: Pi 4 or newer, running Raspberry Pi OS)
- Camera module compatible with Picamera2
- Two ATmega microcontrollers (e.g., Arduino Uno/Nano)
- Sensors: DHT22 (air temperature/humidity), DS18B20 (substrate temperature), analog soil moisture sensor
- Pan & tilt servo assembly
- I²C wiring between Raspberry Pi and ATmegas

### Installation

1. **Clone the Repository:**
   ```sh
   git clone https://github.com/your-org/SmartFungi.git
   cd SmartFungi
   ```

2. **Run the Setup Script:**
   The setup script installs system dependencies, creates a Python virtual environment, and installs required Python packages.
   ```sh
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Flash the Microcontrollers:**
   - Upload `Arduino/PanTilt/PanTilt.ino` to the pan/tilt ATmega.
   - Upload `Arduino/SensorsReadings/SensorsReadings.ino` to the sensor ATmega.

4. **Connect Hardware:**
   - Wire the camera module to the Raspberry Pi.
   - Connect the ATmegas to the Pi via I²C (SDA/SCL).
   - Attach sensors and servos as specified in the Arduino sketches.

5. **Start the Server:**
   ```sh
   source .venv/bin/activate
   python Server/app.py
   ```
   The web interface will be available at [http://localhost:5000](http://localhost:5000).

### Configuration

- Edit `Server/config.py` to adjust camera settings, available resolutions, I²C addresses, and feature toggles.

### Usage

- Access the web interface to:
  - View live video and environmental data.
  - Control camera orientation.
  - Capture images or start/stop timelapse sessions.
  - Download captured images and review sensor history.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- [Picamera2](https://github.com/raspberrypi/picamera2)
- [Flask](https://flask.palletsprojects.com/)
- [OpenCV](https://opencv.org/)

---

For further details, refer to the source code and comments in each module.