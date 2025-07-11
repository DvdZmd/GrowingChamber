#!/bin/bash

#-------------------------------------------
# Growing Chamber Setup Script
#-------------------------------------------
# This script performs:
#   - System package updates and dependency installation
#   - Python virtual environment creation and setup
#   - Python dependencies installation
#   - Optional systemd service configuration and startup
#-------------------------------------------

echo "Updating system packages..."
sudo apt update

# Install required system packages for camera and Python development
echo "Installing required system dependencies..."
sudo apt install -y libcamera-dev libcamera-apps python3-libcamera
sudo apt install -y python3-venv python3-dev libcap-dev libatlas-base-dev libopenjp2-7 libtiff-dev cmake

#-------------------------------------------
# Python virtual environment setup
#-------------------------------------------

if [ -d ".venv" ]; then
    read -p "The .venv virtual environment already exists. Do you want to delete and recreate it? (y/n): " answer
    if [[ "$answer" =~ ^[yY]$ ]]; then
        echo "Deleting existing virtual environment..."
        rm -rf .venv
    else
        echo "Using the existing virtual environment."
    fi
fi

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment with access to system packages..."
    python3 -m venv .venv --system-site-packages
fi

echo "Activating virtual environment and installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip

echo "Uninstalling system-wide numpy to avoid conflicts with venv..."
sudo apt remove -y python3-numpy

pip install --upgrade numpy
pip uninstall -y simplejpeg picamera2
pip install simplejpeg picamera2

pip install -r requirements.txt

read -p "Setup complete. Do you want to activate the virtual environment now? (y/n): " activate_env
if [[ "$activate_env" =~ ^[yY]$ ]]; then
    source .venv/bin/activate
    echo "Virtual environment activated."
else
    echo "You can activate the environment later with: source .venv/bin/activate"
fi

#-------------------------------------------
# systemd service setup
#-------------------------------------------

echo "Starting the growing chamber service configuration..."

read -p "Do you want to set up growingchamber.service in systemd to start on boot? (y/n): " setup_choice
if [[ "$setup_choice" =~ ^[Yy]$ ]]; then
    export GROWINGCHAMBER_PATH="$(pwd)"
    echo "Detected repository path: $GROWINGCHAMBER_PATH"

    echo "Rendering systemd service file with correct path..."
    envsubst < growingchamber.service.in > /tmp/growingchamber.service

    echo "Installing systemd service file..."
    sudo cp /tmp/growingchamber.service /etc/systemd/system/growingchamber.service

    echo "Reloading systemd to recognize the new service..."
    sudo systemctl daemon-reload

    echo "Enabling the service to start on boot..."
    sudo systemctl enable growingchamber.service
    echo "Service enabled to start on boot."
else
    echo "Skipped systemd setup."
fi

read -p "Do you want to start the growingchamber.service now? (y/n): " start_choice
if [[ "$start_choice" =~ ^[Yy]$ ]]; then
    echo "Starting the service..."
    sudo systemctl start growingchamber.service
    echo "Service started successfully."
else
    echo "Skipped starting the service now."
fi

#-------------------------------------------
# Final notes
#-------------------------------------------
echo
echo "You can always manage the service with the following commands:"
echo "  To start the service:   sudo systemctl start growingchamber.service"
echo "  To stop the service:    sudo systemctl stop growingchamber.service"
echo "  To check the status:    sudo systemctl status growingchamber.service"
echo "  To view the logs:       journalctl -u growingchamber.service -f"
