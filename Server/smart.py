import tinytuya
from config import SMARTPLUG_DEVICE_ID, SMARTPLUG_IP, SMARTPLUG_LOCAL_KEY, SMARTPLUG_PROTOCOL_VERSION

def get_smartplug():
    plug = tinytuya.OutletDevice(SMARTPLUG_DEVICE_ID, SMARTPLUG_IP, SMARTPLUG_LOCAL_KEY)
    plug.set_version(SMARTPLUG_PROTOCOL_VERSION)
    return plug

def get_status():
    plug = get_smartplug()
    status = plug.status()
    # Typical Tuya plugs: dps 1 is on/off
    return status.get('dps', {}).get('1', False)

def turn_on():
    plug = get_smartplug()
    return plug.turn_on()

def turn_off():
    plug = get_smartplug()
    return plug.turn_off()