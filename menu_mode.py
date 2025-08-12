from __future__ import annotations

import cv2
import sys
import time
from typing import Optional
import platform

import mediapipe as mp

WINDOW_TITLE = "Menu por Gestos (Izq=QR | Der=Gestos/Juego)"
WIN_W, WIN_H = 960, 540
MIRROR = True

# Zonas de selección (en proporción del ancho)
LEFT_MAX_X  = 0.40   # < 40% de ancho -> IZQUIERDA (QR)
RIGHT_MIN_X = 0.60   # > 60% de ancho -> DERECHA  (Gestos/Juego)

DWELL_SECONDS = 1.2  # tiempo de permanencia para confirmar selección
MIN_CONFIDENCE_DET = 0.7
MIN_CONFIDENCE_TRACK = 0.6

BAR_H = 12  # alto de la barra de progreso

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def _draw_layout(frame, progress_left: float, progress_right: float):
    h, w = frame.shape[:2]
    # Divisiones visuales
    c_left  = (70, 170, 255)
    c_right = (60, 255, 160)
    # Columnas semi transparentes
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (int(w*LEFT_MAX_X), h), c_left, -1)
    cv2.rectangle(overlay, (int(w*RIGHT_MIN_X), 0), (w, h), c_right, -1)
    cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)

    # Títulos
    cv2.putText(frame, "IZQUIERDA -> Modo QR", (20, 36),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
    cv2.putText(frame, "DERECHA  -> Gestos/Juego", (w - 380, 36),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

    # Barras de progreso
    if progress_left > 0:
        filled = int((w * 0.45) * max(0.0, min(1.0, progress_left)))
        cv2.rectangle(frame, (20, h - 30), (20 + filled, h - 30 + BAR_H), c_left, -1)
        cv2.rectangle(frame, (20, h - 30), (20 + int(w*0.45), h - 30 + BAR_H), (255,255,255), 1)

    if progress_right > 0:
        total = int(w * 0.45)
        x0 = w - 20 - total
        filled = int(total * max(0.0, min(1.0, progress_right)))
        cv2.rectangle(frame, (x0, h - 30), (x0 + filled, h - 30 + BAR_H), c_right, -1)
        cv2.rectangle(frame, (x0, h - 30), (x0 + total, h - 30 + BAR_H), (255,255,255), 1)

    # Indicaciones
    cv2.putText(frame, "Mantene la mano en un lado ~1.2s para elegir",
                (20, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230,230,230), 1)
    cv2.putText(frame, "Atajos: 'q'=QR | 'g'=Gestos | 'ESC'/'q'=Salir",
                (20, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220,220,220), 1)

def run(camera_index: int = 0) -> Optional[str]:
    """
    Devuelve:
      - "qr"     si el usuario eligio la zona izquierda
      - "gestos" si el usuario eligio la zona derecha
      - None     si el usuario sale (ESC / q)
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara para el menú")
        return None

    cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_TITLE, WIN_W, WIN_H)

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=MIN_CONFIDENCE_DET,
        min_tracking_confidence=MIN_CONFIDENCE_TRACK,
    )

    dwell_side: Optional[str] = None   # "left" | "right" | None
    dwell_start: float = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if MIRROR:
                frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (WIN_W, WIN_H))

            # Detección de mano
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)

            side = None
            progress_left = 0.0
            progress_right = 0.0

            if res.multi_hand_landmarks:
                lms = res.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(frame, lms, mp_hands.HAND_CONNECTIONS)

                # Usa la muñeca (landmark 0) para decidir lado
                wrist = lms.landmark[0]
                x_norm = wrist.x  # 0..1 tras flip/resize
                if x_norm <= LEFT_MAX_X:
                    side = "left"
                elif x_norm >= RIGHT_MIN_X:
                    side = "right"

            now = time.time()

            if side is None:
                dwell_side = None
                dwell_start = 0.0
            else:
                if dwell_side != side:
                    # comienza dwell en nuevo lado
                    dwell_side = side
                    dwell_start = now
                # progreso
                t = now - dwell_start
                p = min(1.0, t / DWELL_SECONDS)
                if side == "left":
                    progress_left = p
                else:
                    progress_right = p

                if t >= DWELL_SECONDS:
                    # Confirmado
                    selection = "qr" if side == "left" else "gestos"
                    cap.release()
                    cv2.destroyWindow(WINDOW_TITLE)
                    return selection

            # UI
            _draw_layout(frame, progress_left, progress_right)
            cv2.imshow(WINDOW_TITLE, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q')):   # salir
                cap.release()
                cv2.destroyWindow(WINDOW_TITLE)
                return None
            if key == ord('k'):         # también permitir volver (sale)
                cap.release()
                cv2.destroyWindow(WINDOW_TITLE)
                return None
            if key == ord('g'):         # atajo: gestos
                cap.release()
                cv2.destroyWindow(WINDOW_TITLE)
                so = platform.system()
                if so == "Windows":
                    return "gestosWindows"
                elif so == "Linux":
                    return "gestosLinux"
            if key == ord('q'):         # atajo: qr
                cap.release()
                cv2.destroyWindow(WINDOW_TITLE)
                return "qr"

    finally:
        cap.release()
        cv2.destroyAllWindows()
