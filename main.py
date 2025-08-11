from __future__ import annotations

import sys
import time
import serial

import qr_mode
import gesture_mode

PORT = "/dev/ttyUSB0"
BAUD = 9600


def main() -> None:
    try:
        arduino = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)
        arduino.reset_input_buffer()
        print("Arduino conectado en", PORT)
    except serial.SerialException as e:
        print("Error puerto serial:", e)
        sys.exit(1)

    modo = "gestos"
    try:
        while True:
            if modo == "qr":
                qr_mode.run(arduino)
                modo = "gestos"
            else:
                gesture_mode.run(arduino)
                modo = "qr"
    finally:
        if arduino.is_open:
            gesture_mode.control_led(arduino, "off")
            arduino.close()
            print("Puerto serie cerrado")


if __name__ == "__main__":
    main()