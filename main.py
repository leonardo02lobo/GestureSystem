from __future__ import annotations

import time
import serial
import tkinter as tk

import menu_mode
import qr_mode
import gesture_mode     # gestos con Arduino opcional
import gesture_mode2    # minijuego
import camera_capture   # ← NUEVO

root = tk.Tk()
root.withdraw()

def main() -> None:
    print("App iniciada. ESC para salir desde el menú.")

    try:
        # Conectar Arduino (si está en Linux con el puerto correcto)
        try:
            arduino = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
            time.sleep(2)
            print("Arduino conectado en /dev/ttyUSB0")
        except serial.SerialException:
            arduino = None
            print("⚠ No se pudo conectar con Arduino.")

        while True:
            choice = menu_mode.run()  # 'qr' | 'juego' | 'gestos' | 'foto' | None
            if choice is None:
                break

            if choice == "qr":
                qr_mode.run()
            elif choice == "juego":
                gesture_mode2.run()
            elif choice == "foto":
                # Lanza captura de foto (usa su propia ventana/cámara)
                camera_capture.capture_photo()
            else:  # 'gestos'
                # Pasa el objeto Arduino si está disponible
                gesture_mode.run(arduino)

    except KeyboardInterrupt:
        pass
    finally:
        print("Aplicación cerrada")

if __name__ == "__main__":
    main()
