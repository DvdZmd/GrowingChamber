from picamera2 import Picamera2, Preview
from config import FRAME_RATE, NOISE_REDUCTION_MODE, CAMERA_WIDTH, CAMERA_HEIGHT

picam2 = None
video_config = None

try:
    picam2 = Picamera2()
    controls = {
        "FrameRate": FRAME_RATE,
        "NoiseReductionMode": NOISE_REDUCTION_MODE
    }

    available_controls = picam2.camera_controls
    if "AfMode" in available_controls:
        controls["AfMode"] = 2  # Continuous autofocus

    video_config = picam2.create_video_configuration(
        main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT)},
        controls=controls
    )

    picam2.configure(video_config)
    picam2.start()
    print("[Camera] Cámara iniciada correctamente.")
except Exception as e:
    print(f"[Camera] No se pudo iniciar la cámara: {e}")
