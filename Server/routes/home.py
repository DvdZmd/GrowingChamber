from flask import Blueprint, render_template
from config import AVAILABLE_RESOLUTIONS, READ_SENSORS, READ_SERVOS, INVERT_PAN_AXIS, INVERT_TILT_AXIS

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    return render_template('index.html', 
                           resolutions=AVAILABLE_RESOLUTIONS, 
                           read_sensors=READ_SENSORS, 
                           read_servos=READ_SERVOS,
                           inverted_pan = INVERT_PAN_AXIS,
                           inverted_tilt = INVERT_TILT_AXIS)
