from __future__ import annotations

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
                    gesture_mode.run()  
                except Exception:   
                    messagebox.showinfo("Espera", "No reconoce el arduino")
    except KeyboardInterrupt:
        pass
    finally:
        print("Aplicación cerrada")

if __name__ == "__main__":
    main()
