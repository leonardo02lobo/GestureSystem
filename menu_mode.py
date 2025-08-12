from __future__ import annotations

import cv2
import time
from typing import Optional
import mediapipe as mp

WINDOW_TITLE = "Menu por Gestos (4 cuadrantes)"
WIN_W, WIN_H = 1200, 960   # Ahora cuadrada
MIRROR = True

DWELL_SECONDS = 1.2
MIN_CONFIDENCE_DET = 0.7
MIN_CONFIDENCE_TRACK = 0.6

FULLSCREEN = True
_is_fullscreen = False

COLOR_TL = (70, 170, 255)   # QR (TL)
COLOR_TR = (60, 255, 160)   # JUEGO (TR)
COLOR_BL = (255, 200, 90)   # FOTO (BL)
COLOR_BR = (255, 180, 60)   # GESTOS (BR)
COLOR_TXT = (255, 255, 255)
BAR_H = 12

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


def _quadrant_of(x_norm: float, y_norm: float) -> str:
    left = x_norm < 0.5
    top = y_norm < 0.5
    if top and left:
        return "TL"
    if top and not left:
        return "TR"
    if not top and left:
        return "BL"
    return "BR"


def _draw_overlay(frame, q: Optional[str], progress: float):
    h, w = frame.shape[:2]
    half_w, half_h = w // 2, h // 2

    overlay = frame.copy()

    def fill(rect, color):
        x0, y0, x1, y1 = rect
        cv2.rectangle(overlay, (x0, y0), (x1, y1), color, -1)

    fill((0, 0, half_w, half_h), COLOR_TL)  # TL
    fill((half_w, 0, w, half_h), COLOR_TR)  # TR
    fill((0, half_h, half_w, h), COLOR_BL)  # BL
    fill((half_w, half_h, w, h), COLOR_BR)  # BR

    cv2.addWeighted(overlay, 0.13, frame, 0.87, 0, frame)
    cv2.line(frame, (half_w, 0), (half_w, h), (255, 255, 255), 1)
    cv2.line(frame, (0, half_h), (w, half_h), (255, 255, 255), 1)

    cv2.putText(frame, "QR", (20, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLOR_TXT, 2)
    cv2.putText(frame, "JUEGO", (w - 160, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLOR_TXT, 2)
    cv2.putText(frame, "FOTO", (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLOR_TXT, 2)
    cv2.putText(frame, "GESTOS", (w - 180, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLOR_TXT, 2)

    if q is not None:
        total = int(w * 0.38)
        filled = int(total * max(0.0, min(1.0, progress)))
        pad = 20
        if q == "TL":
            x0, y0 = pad, pad
            color = COLOR_TL
        elif q == "TR":
            x0, y0 = w - pad - total, pad
            color = COLOR_TR
        elif q == "BL":
            x0, y0 = pad, h - pad - BAR_H
            color = COLOR_BL
        else:
            x0, y0 = w - pad - total, h - pad - BAR_H
            color = COLOR_BR

        cv2.rectangle(frame, (x0, y0), (x0 + filled, y0 + BAR_H), color, -1)
        cv2.rectangle(frame, (x0, y0), (x0 + total, y0 + BAR_H), (255, 255, 255), 1)

    cv2.putText(frame, "Mantene la mano ~1.2s en un cuadrante para seleccionar",
                (20, h // 2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 2)
    cv2.putText(frame, "Atajos: 1=QR | 2=Juego | 3=Gestos | 4=Foto | ESC salir | f Fullscreen",
                (20, h // 2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)


def _set_fullscreen(enable: bool):
    global _is_fullscreen
    try:
        cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_TITLE, WIN_W, WIN_H) 
        _is_fullscreen = enable
    except Exception:
        cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_TITLE, WIN_W, WIN_H)
        _is_fullscreen = False


def run(camera_index: int = 0) -> Optional[str]:
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara para el menú")
        return None

    # También fijamos resolución de captura
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIN_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WIN_H)

    _set_fullscreen(FULLSCREEN)

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=MIN_CONFIDENCE_DET,
        min_tracking_confidence=MIN_CONFIDENCE_TRACK,
    )

    dwell_q: Optional[str] = None
    dwell_start: float = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if MIRROR:
                frame = cv2.flip(frame, 1)

            frame = cv2.resize(frame, (WIN_W, WIN_H))

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)

            q_active: Optional[str] = None
            progress = 0.0

            if res.multi_hand_landmarks:
                lms = res.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(frame, lms, mp_hands.HAND_CONNECTIONS)

                wrist = lms.landmark[0]
                x_norm, y_norm = wrist.x, wrist.y
                q_active = _quadrant_of(x_norm, y_norm)

                now = time.time()
                if dwell_q != q_active:
                    dwell_q = q_active
                    dwell_start = now
                elapsed = now - dwell_start
                progress = min(1.0, elapsed / DWELL_SECONDS)

                if elapsed >= DWELL_SECONDS:
                    sel_map = {"TL": "qr", "TR": "juego", "BR": "gestos", "BL": "foto"}
                    selection = sel_map.get(q_active)
                    if selection is not None:
                        cap.release()
                        cv2.destroyWindow(WINDOW_TITLE)
                        return selection
                    else:
                        dwell_q = None
                        dwell_start = 0.0
            else:
                dwell_q = None
                dwell_start = 0.0

            _draw_overlay(frame, q_active, progress)
            cv2.imshow(WINDOW_TITLE, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q')):
                cap.release()
                cv2.destroyWindow(WINDOW_TITLE)
                return None
            if key == ord('1'):
                cap.release(); cv2.destroyWindow(WINDOW_TITLE); return "qr"
            if key == ord('2'):
                cap.release(); cv2.destroyWindow(WINDOW_TITLE); return "juego"
            if key == ord('3'):
                cap.release(); cv2.destroyWindow(WINDOW_TITLE); return "gestos"
            if key == ord('4'):
                cap.release(); cv2.destroyWindow(WINDOW_TITLE); return "foto"
            if key == ord('f'):
                _set_fullscreen(not _is_fullscreen)
    finally:
        cap.release()
        cv2.destroyAllWindows()
