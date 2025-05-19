const apiUrl = `${window.location.protocol}//${window.location.hostname}:5000`;
let servo_pan = 90;
let servo_tilt = 90;

function updateServoDisplay() {
  document.getElementById("servo_pan_value").textContent = servo_pan;
  document.getElementById("servo_tilt_value").textContent = servo_tilt;
}   

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function moveServo(pan, tilt) {

  if(read_servos == false)
    return;

  servo_tilt = Math.max(90, Math.min(160, tilt));
  servo_pan = Math.max(0, Math.min(180, pan));

  try {
    const response = await fetch(`${apiUrl}/send_pan_tilt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pan: servo_pan, tilt: servo_tilt }),
    });

    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
        updateServoDisplay();

  } catch (error) {
    console.error("Error:", error);
  }
}

async function fetchSensorData() {
  try {
    const response = await fetch(`${apiUrl}/get_sensors`);

    if (!response.ok) 
        throw new Error(`HTTP error: ${response.status}`);

    const data = await response.json();
    document.getElementById("temperature_dht").textContent = data.temperature_dht;
    document.getElementById("humidity").textContent = data.humidity;
    document.getElementById("temperature_ds18b20").textContent = data.temperature_ds18b20;
    document.getElementById("soil_moisture").textContent = data.soil_moisture;
  } catch (error) {
    console.error("Error fetching sensor data:", error);
  }
}

async function fetchServoPosition() {
  try {
    const response = await fetch(`${apiUrl}/request_current_pan_tilt`);

    if (!response.ok) 
        throw new Error(`HTTP error: ${response.status}`);

    const data = await response.json();
    servo_pan = data.pan;
    servo_tilt = data.tilt;
    updateServoDisplay();

  } catch (error) {
    console.error("Error fetching servo position:", error);
  }
}

window.onload = () => {

  let timelapseActive = false;
  document.getElementById("btn-up").addEventListener("click", () => {
    const tiltStep = inverted_tilt ? -5 : 5;
    moveServo(servo_pan, servo_tilt + tiltStep );
  });
  document.getElementById("btn-down").addEventListener("click", () => {
    const tiltStep = inverted_tilt ? 5 : -5;
      moveServo(servo_pan, servo_tilt + tiltStep);
  });
  document.getElementById("btn-left").addEventListener("click", () => {
      const panStep = inverted_pan ? -5 : 5;
      moveServo(servo_pan + panStep, servo_tilt);
  });
  document.getElementById("btn-right").addEventListener("click", () => {
    const panStep = inverted_pan ? 5 : -5;
    moveServo(servo_pan + panStep, servo_tilt);
  });
  document.getElementById("videoFeed").src = `${apiUrl}/video_feed`;
  document.getElementById("timelapseToggleBtn").addEventListener("click", async () => {
    const interval = parseInt(document.getElementById("timelapseInterval").value);
    const [width, height] = document
      .getElementById("timelapseResolution").value
      .split("x")
      .map(Number);

    try {
      const response = await fetch(`${apiUrl}/timelapse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          action: timelapseActive ? "stop" : "start",
          interval_minutes: interval,
          width,
          height
        })
      });

      const data = await response.json();
      document.getElementById("timelapseStatus").textContent = data.message;

      timelapseActive = !timelapseActive;
      document.getElementById("timelapseToggleBtn").textContent = timelapseActive
        ? "Stop Timelapse"
        : "Start Timelapse";
    } catch (error) {
      console.error("Error toggling timelapse:", error);
      document.getElementById("timelapseStatus").textContent = "❌ Error communicating with server";
    }
  });
  document.getElementById("captureBtn").addEventListener("click", async () => {
    const resolutionValue = document.getElementById("resolutionSelect").value;
    console.log("resolutionValue: ", resolutionValue);

    const [width, height] = resolutionValue.split("x").map(Number);

    try {
      const response = await fetch(`${apiUrl}/capture_image?width=${width}&height=${height}&download=true`);
      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `image_${width}x${height}.jpg`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      document.getElementById("captureStatus").textContent = `✅ Downloaded image at ${width}x${height}`;
    } catch (error) {
      console.error("Download error:", error);
      document.getElementById("captureStatus").textContent = "❌ Error downloading image";
    }
  });



  let cameraEnabled = true;

  document.getElementById("toggleCameraBtn").addEventListener("click", async () => {
    try {
      const res = await fetch(`${apiUrl}/toggle_camera`, {
        method: "POST"
      });
      const data = await res.json();
      cameraEnabled = data.enabled;
      document.getElementById("toggleCameraBtn").textContent = cameraEnabled
        ? "Turn Camera Off"
        : "Turn Camera On";
      document.getElementById("cameraStatus").textContent = data.message;

      // Optional: Hide or show the feed
      document.getElementById("videoFeed").style.display = cameraEnabled ? "block" : "none";
    } catch (error) {
      console.error("Camera toggle error:", error);
      document.getElementById("cameraStatus").textContent = "❌ Error toggling camera";
    }
  });

  document.getElementById('rotationSelect').addEventListener('change', function () {
    const angle = this.value;
    fetch('/set_rotation', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: `angle=${angle}`
    })
    .then(res => res.text())
    .then(console.log)
    .catch(console.error);
  });

if(read_sensors)
  setInterval(fetchSensorData, 500);
if(read_servos)
  setInterval(fetchServoPosition, 200);
};