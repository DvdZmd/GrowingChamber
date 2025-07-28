from flask import Blueprint, render_template, redirect, url_for, session
from config import AVAILABLE_RESOLUTIONS, READ_SENSORS, READ_SERVOS, INVERT_PAN_AXIS, INVERT_TILT_AXIS

home_bp = Blueprint('home', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@home_bp.route('/')
@login_required
def index():
    return render_template('index.html', 
                           resolutions=AVAILABLE_RESOLUTIONS, 
                           read_sensors=READ_SENSORS, 
                           read_servos=READ_SERVOS,
                           inverted_pan = INVERT_PAN_AXIS,
                           inverted_tilt = INVERT_TILT_AXIS)
