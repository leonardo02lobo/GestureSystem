from __future__ import annotations

import sys
import time
import platform
import tkinter as tk
from tkinter import messagebox  

import menu_mode
import qr_mode
import gesture_mode      # ← minijuego (Fruit Ninja)
import gesture_mode2     # ← “gestos” clásicos (si lo tienes; si no, usa gesture_mode)

root = tk.Tk()
root.withdraw() 

def main() -> None:
    print("App iniciada. ESC para salir desde el menú.")

    try:
        while True:
            choice = menu_mode.run()  # 'qr' | 'juego' | 'gestos' | None
            if choice is None:
                break

            if choice == "qr":
                qr_mode.run()
            elif choice == "juego":
                gesture_mode2.run()       # ← si tu juego está aquí
            else:  # 'gestos'
                try:
                    gesture_mode.run()  # ← si tienes otro modo de gestos
                except Exception:   
                    # si no existe, usa el mismo juego como placeholder
                    messagebox.showinfo("Espera", "No reconoce el arduino")
    except KeyboardInterrupt:
        pass
    finally:
        print("Aplicación cerrada")

if __name__ == "__main__":
    main()
