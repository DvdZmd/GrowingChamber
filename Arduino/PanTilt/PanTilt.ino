#include <Wire.h>
#include <Servo.h>

#define I2C_ADDRESS 0x10  // Unique I2C address for this Arduino
#define LED_PIN 13  // Built-in LED pin


Servo panServo;
Servo tiltServo;

int panAngle = 90;  // Default position
int tiltAngle = 90;
int randomRead = 0;

void setup() {
    Wire.begin(I2C_ADDRESS);  // Join I2C bus as a slave
    Wire.onReceive(receiveEvent);
    Wire.onRequest(requestEvent);  // Set callback for data requested

    panServo.attach(5);
    tiltServo.attach(6);
    
    panServo.write(panAngle);
    tiltServo.write(tiltAngle);
}

void loop() {
    // No need for code here; servos update on I2C commands
}

// Callback function for I2C data reception
void receiveEvent(int bytes) {

    if (Wire.available() >= 2) {  // Expecting two bytes (pan, tilt)
        randomRead = Wire.read();  // Read first byte (pan angle)
        panAngle = Wire.read(); // Read second byte (tilt angle)
        tiltAngle = Wire.read(); // Read second byte (tilt angle)

        panAngle = constrain(panAngle, 85, 170);
        tiltAngle = constrain(tiltAngle, 0, 180);

        panServo.write(panAngle);
        tiltServo.write(tiltAngle);
    }
}

// Callback function for I2C data request
void requestEvent() {
    Wire.write(panAngle);   // Send current pan angle
    Wire.write(tiltAngle);  // Send current tilt angle
}
