from datetime import datetime
import os
from threading import Event, Thread
import time
from flask import Blueprint, Response, request, send_file, jsonify
from config import AVAILABLE_RESOLUTIONS
from camera.picam import picam2
# from camera.timelapse import TimelapseThread
from camera.picam import video_config
import cv2

camera_bp = Blueprint('camera', __name__)
timelapse_thread = None
timelapse_stop_event = Event()

# ======= CAMERA STREAM FUNCTION ===========
def generate_frames():
    if not picam2:
        print("[Stream] Cámara no disponible.")
        return

    while True:
        frame = picam2.capture_array()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rotated = cv2.rotate(frame_rgb, cv2.ROTATE_180)
        _, buffer = cv2.imencode('.jpg', frame_rotated)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

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
            still_config = picam2.create_still_configuration(main={"size": resolution})
            picam2.configure(still_config)
            picam2.start()
            time.sleep(0.5)


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
        time.sleep(0.5)

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
