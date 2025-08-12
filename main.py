import time
import serial
import tkinter as tk
from tkinter import messagebox  

import menu_mode
import qr_mode
import gesture_mode    
import gesture_mode2   

root = tk.Tk()
root.withdraw() 

def main() -> None:
    print("App iniciada. ESC para salir desde el menú.")

    try:
        # Intentar conectar con Arduino
        try:
            arduino = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
            time.sleep(2)  # Espera a que Arduino reinicie
        except serial.SerialException:
            arduino = None
            print("⚠ No se pudo conectar con Arduino.")

        while True:
            choice = menu_mode.run() 
            if choice is None:
                break

            if choice == "qr":
                qr_mode.run()
            elif choice == "juego":
                gesture_mode2.run()    
            else: 
                try:
                    gesture_mode.run(arduino)  # ← Ahora le pasamos el Arduino
                except Exception:
                    # messagebox.showinfo("Espera", "No reconoce el arduino")
                    gesture_mode.run(arduino)  
    except KeyboardInterrupt:
        pass
    finally:
        print("Aplicación cerrada")

if __name__ == "__main__":
    main()
