from flask import Flask
from routes.home import home_bp
from routes.camera_routes import camera_bp
from routes.i2c_routes import i2c_bp
from database.database import init_db

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(home_bp)
app.register_blueprint(camera_bp)
app.register_blueprint(i2c_bp)

# Initialize the database
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
