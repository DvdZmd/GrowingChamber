from flask import Blueprint, jsonify, request
from smart import get_status, turn_on, turn_off

smartplug_bp = Blueprint('smartplug', __name__)

@smartplug_bp.route('/smartplug/status', methods=['GET'])
def smartplug_status():
    try:
        status = get_status()
        return jsonify({"status": status})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@smartplug_bp.route('/smartplug/toggle', methods=['POST'])
def smartplug_toggle():
    try:
        data = request.get_json()
        action = data.get('action')
        if action == 'on':
            retorno = turn_on()
        elif action == 'off':
            retorno = turn_off()
        else:
            return jsonify({"error": "Invalid action"}), 400
        return jsonify({"result": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500