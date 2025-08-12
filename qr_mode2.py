from __future__ import annotations

import cv2
import subprocess
import webbrowser
import time
import sys
from pyzbar.pyzbar import decode

WINDOW_QR = "Modo QR"


def ventana_tiene_focus(expected_name: str) -> bool:
    """
    Devuelve True si la ventana activa contiene expected_name.
    Requiere xdotool (NO compatible con Wayland). En Wayland devolvemos True.
    """
    try:
        name = subprocess.check_output(
            ["xdotool", "getactivewindow", "getwindowname"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return expected_name in name
    except Exception:
        # En Wayland / sin xdotool, no pausamos por foco.
        return True


def run(camera_index: int = 0) -> None:
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara para el modo QR")
        return

    cv2.namedWindow(WINDOW_QR, cv2.WINDOW_NORMAL)
    print("[ MODO QR ] Presiona 'k' para cambiar de modo | 'q' o ESC para salir")

    bloqueado = False
    ultimo_url: str | None = None
    ultimo_open = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        cv2.imshow(WINDOW_QR, frame)

        # Si la ventana fue cerrada manualmente
        if cv2.getWindowProperty(WINDOW_QR, cv2.WND_PROP_VISIBLE) < 1:
            break

        # Pausar si no hay foco (solo X11)
        if not ventana_tiene_focus(WINDOW_QR):
            if not bloqueado:
                print("🔒 Ventana sin focus — escaneo pausado")
                bloqueado = True
            key = cv2.waitKey(100) & 0xFF
            if key == ord("k"):
                break
            if key in (27, ord("q")):
                cap.release()
                cv2.destroyWindow(WINDOW_QR)
                sys.exit(0)
            continue
        else:
            if bloqueado:
                print("✅ Ventana con focus — escaneo reanudado")
                bloqueado = False

        if not bloqueado:
            # Decodifica en BGR (podrías acelerar pasando a escala de grises)
            for qr in decode(frame):
                url = qr.data.decode().strip()
                ahora = time.time()
                # Evita reabrir el mismo URL en < 3s
                if url == ultimo_url and ahora - ultimo_open < 3:
                    continue
                print("QR:", url)
                ultimo_url, ultimo_open = url, ahora

                # Validación simple de URL (opcional)
                if url.startswith(("http://", "https://")):
                    webbrowser.open(url)
                else:
                    print("⚠️ Contenido QR no es URL http/https; no se abre automáticamente.")

                bloqueado = True  # Evita escanear repetidamente hasta cambiar foco
                break

        key = cv2.waitKey(1) & 0xFF
        if key == ord("k"):
            break
        if key in (27, ord("q")):
            cap.release()
            cv2.destroyWindow(WINDOW_QR)
            sys.exit(0)

    cap.release()
    cv2.destroyWindow(WINDOW_QR)
