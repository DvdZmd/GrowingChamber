from picamera2 import Picamera2, Preview
from config import FRAME_RATE, NOISE_REDUCTION_MODE

picam2 = None
video_config = None

try:
    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(
        main={"size": (2000, 2000)},
        controls={"FrameRate": FRAME_RATE, "NoiseReductionMode": NOISE_REDUCTION_MODE}
    )
    picam2.configure(video_config)
    picam2.start()
    print("[Camera] Cámara iniciada correctamente.")
except Exception as e:
    print(f"[Camera] No se pudo iniciar la cámara: {e}")
