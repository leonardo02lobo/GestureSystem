from __future__ import annotations

import sys
import menu_mode
import qr_mode
import gesture_mode2

def main() -> None:
    print("App iniciada. ESC / q para salir desde cualquier modo.")

    try:
        while True:
            # 1) Mostrar menú inicial por gestos y obtener selección
            choice = menu_mode.run()  # "qr" | "gestos" | None (si usuario sale)
            if choice is None:
                break

            # 2) Ejecutar el modo seleccionado
            if choice == "qr":
                qr_mode.run()        # retorna con 'k' para volver al menú
            else:
                gesture_mode2.run()   # retorna con 'k' para volver al menú

    except KeyboardInterrupt:
        pass
    finally:
        print("Aplicación cerrada")

if __name__ == "__main__":
    main()
