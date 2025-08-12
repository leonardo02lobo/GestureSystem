# camera_capture.py
from __future__ import annotations
import cv2
import os
import time
import datetime

WINDOW_TITLE = "Captura de Foto"
FULLSCREEN = True          # pantalla completa ON/OFF
MIRROR = True              # espejo horizontal para control natural
COUNTDOWN_SECONDS = 3      # segundos de conteo antes de capturar
FLASH_MS = 120             # duración del flash visual al capturar

def _set_fullscreen():
    try:
        cv2.namedWindow(WINDOW_TITLE, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(WINDOW_TITLE, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    except Exception:
        cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)

def _draw_centered_text(frame, text: str, scale=3.5, thickness=6, color=(255,255,255), shadow=(0,0,0)):
    h, w = frame.shape[:2]
    (tw, th), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    x = (w - tw) // 2
    y = (h + th) // 2
    if shadow:
        cv2.putText(frame, text, (x+2, y+2), cv2.FONT_HERSHEY_SIMPLEX, scale, shadow, thickness+2, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)

def capture_photo(save_dir="photos", camera_index: int = 0):
    """
    Abre la cámara, muestra un conteo de 3s, toma la foto automáticamente y cierra.
    - ESC durante el conteo: cancelar y volver al menú.
    Devuelve la ruta del archivo guardado o None si se canceló.
    """
    os.makedirs(save_dir, exist_ok=True)

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ No se pudo acceder a la cámara.")
        return None

    if FULLSCREEN:
        _set_fullscreen()
    else:
        cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)

    print(f"📸 Iniciando conteo de {COUNTDOWN_SECONDS} segundos... (ESC para cancelar)")

    filepath = None
    start = time.time()
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error al leer la imagen de la cámara.")
                break

            if MIRROR:
                frame = cv2.flip(frame, 1)

            # Tiempo restante
            elapsed = time.time() - start
            remaining = int(max(0, COUNTDOWN_SECONDS - elapsed) + 0.999)  # ceil visual

            # Dibujar overlay de conteo
            if remaining > 0:
                _draw_centered_text(frame, str(remaining))
                cv2.putText(frame, "ESC: Cancelar",
                            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2, cv2.LINE_AA)
                cv2.imshow(WINDOW_TITLE, frame)
            else:
                # Capturar (flash opcional)
                flash = frame.copy()
                flash[:] = (255, 255, 255)
                cv2.imshow(WINDOW_TITLE, flash)
                cv2.waitKey(FLASH_MS)

                # Guardar
                filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
                filepath = os.path.join(save_dir, filename)
                cv2.imwrite(filepath, frame)
                print(f"✅ Foto guardada en {filepath}")
                break

            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("🚪 Captura cancelada por el usuario.")
                filepath = None
                break

    finally:
        cap.release()
        cv2.destroyWindow(WINDOW_TITLE)

    return filepath

if __name__ == "__main__":
    capture_photo()
