from __future__ import annotations

import cv2
import subprocess
import webbrowser
import time
import sys
from pyzbar.pyzbar import decode

# ---- Config ventana ----
WINDOW_QR = "Modo QR"
FULLSCREEN = True  # ← pantalla completa ON/OFF

def ventana_tiene_focus(expected_name: str) -> bool:
    """Devuelve True si la ventana activa contiene expected_name (requiere xdotool en Linux/X11)."""
    try:
        name = subprocess.check_output(
            ["xdotool", "getactivewindow", "getwindowname"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return expected_name in name
    except Exception:
        # En Windows o si no hay xdotool, asumimos que sí tiene foco
        return True

def run(arduino: object | None = None, camera_index: int = 0) -> None:
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara para el modo QR")
        return

    # ---- Ventana en pantalla completa ----
    if FULLSCREEN:
        cv2.namedWindow(WINDOW_QR, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(WINDOW_QR, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    else:
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

        # Si la ventana fue cerrada
        if cv2.getWindowProperty(WINDOW_QR, cv2.WND_PROP_VISIBLE) < 1:
            break

        # Pausa si la ventana pierde foco (solo aplica donde xdotool funcione)
        if not ventana_tiene_focus(WINDOW_QR):
            if not bloqueado:
                print("🔒 Ventana sin focus — escaneo pausado")
                bloqueado = True
            key = cv2.waitKey(100) & 0xFF
            if key == ord("k"):
                break
            if key in (27, ord("q")):
                sys.exit(0)
            continue
        else:
            if bloqueado:
                print("✅ Ventana con focus — escaneo reanudado")
                bloqueado = False

        # Escaneo QR
        if not bloqueado:
            for qr in decode(frame):
                url = qr.data.decode()
                ahora = time.time()
                # Evita abrir repetidamente el mismo URL muy seguido
                if url == ultimo_url and (ahora - ultimo_open) < 3:
                    continue
                print("QR:", url)
                ultimo_url, ultimo_open = url, ahora
                webbrowser.open(url)
                bloqueado = True  # bloquea para no leer múltiples veces en el mismo frame
                break

        key = cv2.waitKey(1) & 0xFF
        if key == ord("k"):
            break
        if key in (27, ord("q")):
            sys.exit(0)

    cap.release()
    cv2.destroyWindow(WINDOW_QR)
