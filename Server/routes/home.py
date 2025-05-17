from flask import Blueprint, render_template
from config import AVAILABLE_RESOLUTIONS, READ_SENSORS, READ_SERVOS

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    return render_template('index.html', resolutions=AVAILABLE_RESOLUTIONS, read_sensors=READ_SENSORS, read_servos=READ_SERVOS)
