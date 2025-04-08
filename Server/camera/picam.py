from picamera2 import Picamera2, Preview
from config import FRAME_RATE, NOISE_REDUCTION_MODE

picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={"size": (2000, 2000)},
    controls={"FrameRate": 60, "NoiseReductionMode": 2}
)
picam2.configure(video_config)
picam2.start()
