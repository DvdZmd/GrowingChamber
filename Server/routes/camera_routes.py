from datetime import datetime
import os
from threading import Event, Thread
import time
from flask import Blueprint, Response, request, send_file, jsonify
from config import AVAILABLE_RESOLUTIONS, FRAME_RATE, NOISE_REDUCTION_MODE, CAMERA_WIDTH, CAMERA_HEIGHT
from camera.picam import picam2
# from camera.timelapse import TimelapseThread
from camera.picam import video_config
import cv2
import face_recognition

camera_bp = Blueprint('camera', __name__)
timelapse_thread = None
timelapse_stop_event = Event()
camera_stream_enabled = True  # global control
rotation_angle = 0

@camera_bp.route('/toggle_camera', methods=['POST'])
def toggle_camera():
    global camera_stream_enabled
    camera_stream_enabled = not camera_stream_enabled
    return jsonify({
        "enabled": camera_stream_enabled,
        "message": "Camera turned " + ("on" if camera_stream_enabled else "off")
    })

# ======= CAMERA STREAM FUNCTION ===========
def generate_frames():
    while True:
        if not picam2 or not camera_stream_enabled:
            time.sleep(0.1)
            continue

        try:
            frame = picam2.capture_array()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)



            if rotation_angle == 0:
                frame_rotated = frame_rgb
            elif rotation_angle == 90:
                frame_rotated = cv2.rotate(frame_rgb, cv2.ROTATE_90_CLOCKWISE)
            elif rotation_angle == 180:
                frame_rotated = cv2.rotate(frame_rgb, cv2.ROTATE_180)
            elif rotation_angle == 270:
                frame_rotated = cv2.rotate(frame_rgb, cv2.ROTATE_90_COUNTERCLOCKWISE)

            _, buffer = cv2.imencode('.jpg', frame_rotated)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(f"[Camera Stream Error] {e}")
            break

@camera_bp.route('/set_rotation', methods=['POST'])
def set_rotation():
    global rotation_angle
    try:
        angle = int(request.form['angle'])
        if angle in [0, 90, 180, 270]:
            rotation_angle = angle
            return 'OK', 200
        else:
            return 'Invalid angle', 400
    except Exception as e:
        return f'Error: {e}', 500

@camera_bp.route('/video_feed')
def video_feed():
    if not picam2:
        return "Cámara no disponible", 503
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

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
            controls = {
                "FrameRate": FRAME_RATE,
                "NoiseReductionMode": NOISE_REDUCTION_MODE
            }

            # Check if autofocus is supported
            available_controls = picam2.camera_controls
            if "AfMode" in available_controls:
                controls["AfMode"] = 2  # Continuous autofocus

            timelapse_config = picam2.create_video_configuration(
                main={"size": (width, height)},  # <-- here's the size
                controls=controls
            )
            picam2.configure(timelapse_config)
            picam2.start()
            #time.sleep(0.5)


            image = picam2.capture_array()
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


            # Create timelapse folder structure
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
            timelapse_dir = os.path.join(root_dir, "Pictures", "Timelapse")
            date_folder = datetime.now().strftime("%Y-%m-%d")
            save_folder = os.path.join(timelapse_dir, date_folder)
            os.makedirs(save_folder, exist_ok=True)

            timestamp = datetime.now().strftime("%H-%M-%S")
            filename = f"{timestamp}.jpg"
            filepath = os.path.join(save_folder, filename)

            cv2.imwrite(filepath, image)
            print(f"[Timelapse] Saved: {filepath}")

            time.sleep(1)

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

@camera_bp.route('/timelapse', methods=['POST'])
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


@camera_bp.route('/set_stream_resolution', methods=['POST'])
def set_stream_resolution():
    global video_config, picam2
    try:
        data = request.get_json()
        width, height = map(int, data.get("resolution", "640x480").split("x"))
        resolution = (width, height)
        if resolution not in AVAILABLE_RESOLUTIONS:
            return jsonify({"error": "Unsupported resolution"}), 400

        # Reconfigura la cámara para el nuevo tamaño
        picam2.stop()
        video_config = picam2.create_video_configuration(main={"size": resolution})
        picam2.configure(video_config)
        picam2.start()
        return jsonify({"message": f"Stream resolution set to {width}x{height}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@camera_bp.route('/capture_image', methods=['GET'])
def capture_image():
    if not picam2:
        return jsonify({"error": "La cámara no está disponible"}), 503

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
        #time.sleep(0.5)

        # Capture image
        image = picam2.capture_array()
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Prepare folder structure
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))  # Go up from /Server
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
