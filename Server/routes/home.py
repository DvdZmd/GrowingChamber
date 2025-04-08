from flask import Blueprint, render_template
from config import AVAILABLE_RESOLUTIONS

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    return render_template('index.html', resolutions=AVAILABLE_RESOLUTIONS)
