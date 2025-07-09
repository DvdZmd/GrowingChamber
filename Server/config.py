# config.py

# Default camera resolution
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# List of available camera resolutions (width, height)
AVAILABLE_RESOLUTIONS = [
    (640, 480),
    (800, 600),
    (1280, 720),
    (1920, 1080),
    (2592, 1944),
]

# I2C addresses for Arduino devices
ARDUINO_PAN_TILT = 0x10      # I2C address for pan/tilt servo controller
ARDUINO_SENSORS = 0x20       # I2C address for sensor readings

# Axis inversion flags for servo control
INVERT_PAN_AXIS = False      # Set to True to invert pan axis
INVERT_TILT_AXIS = False     # Set to True to invert tilt axis

# I2C bus configuration
I2C_BUS_ID = 1               # Default I2C bus on Raspberry Pi

# Camera settings
FRAME_RATE = 60              # Camera frame rate (FPS)
NOISE_REDUCTION_MODE = 2     # Camera noise reduction mode

# Flags and intervals for reading sensors and servos
READ_SENSORS = False         # Enable/disable periodic sensor reading
READ_SERVOS = False          # Enable/disable periodic servo reading
READ_SENSORS_INTERVAL = 0.1  # Interval (seconds) for sensor polling
READ_SERVOS_INTERVAL = 0.1   # Interval (seconds) for servo polling

# Smart Plug Configuration (TinyTuya)
SMARTPLUG_DEVICE_ID = 'eb5d91425840aa8405zzlk'  # Tuya device ID
SMARTPLUG_IP = '192.168.1.35'                   # Smart plug IP address
SMARTPLUG_LOCAL_KEY = '$uDY!F9u7!L<O7v+'        # Local key for device authentication
SMARTPLUG_PROTOCOL_VERSION = 3.4                # Tuya protocol version