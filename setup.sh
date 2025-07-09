#!/bin/bash

echo "Updating system packages..."
sudo apt update

echo "Installing required system dependencies..."
sudo apt install -y libcamera-dev libcamera-apps python3-libcamera
sudo apt install -y python3-venv python3-dev libcap-dev libatlas-base-dev libopenjp2-7 libtiff-dev cmake

# Check if the virtual environment already exists
if [ -d ".venv" ]; then
    read -p "The .venv virtual environment already exists. Do you want to delete and recreate it? (y/n): " answer
    if [[ "$answer" =~ ^[yY]$ ]]; then
        echo "Deleting existing virtual environment..."
        rm -rf .venv
    else
        echo "Using the existing virtual environment."
    fi
fi

# Create the virtual environment if it does not exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment with access to system packages..."
    python3 -m venv .venv --system-site-packages
fi

# Activate virtual environment and install Python dependencies
echo "Activating virtual environment and installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip

# Uninstall system-wide numpy to avoid conflicts
echo "Uninstalling system-wide numpy to avoid conflicts..."
sudo apt remove -y python3-numpy

# Upgrade numpy inside the virtual environment
pip install --upgrade numpy

# Reinstall simplejpeg and picamera2
pip uninstall -y simplejpeg picamera2
pip install simplejpeg picamera2

# Install all other dependencies
pip install -r requirements.txt

echo "Setup complete. To activate your environment, run:"
echo "source .venv/bin/activate"