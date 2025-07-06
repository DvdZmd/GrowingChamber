#!/bin/bash

echo "Updating system packages..."
sudo apt update

sudo apt install -y libcamera-dev libcamera-apps python3-libcamera

echo "Installing system dependencies..."
sudo apt install -y python3-venv python3-dev libcap-dev libatlas-base-dev libopenjp2-7 libtiff-dev

# Verifica si el entorno virtual ya existe
if [ -d ".venv" ]; then
    read -p "El entorno virtual .venv ya existe. ¿Quieres borrarlo y crearlo de nuevo? (s/n): " respuesta
    if [[ "$respuesta" =~ ^[sS]$ ]]; then
        echo "Eliminando entorno virtual existente..."
        rm -rf .venv
    else
        echo "Usando el entorno virtual existente."
    fi
fi

# Crea el entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo "Creando entorno virtual de Python con acceso a paquetes del sistema..."
    python3 -m venv .venv --system-site-packages
fi

echo "Activando entorno virtual e instalando dependencias de Python..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup completo. Para activar tu entorno, ejecuta:"
echo "source .venv/bin/activate"