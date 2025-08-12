from __future__ import annotations

import cv2
import subprocess
import webbrowser
import time
import sys
from pyzbar.pyzbar import decode
import mediapipe as mp

# ---- Config ventana ----
WINDOW_QR = "Modo QR"
FULLSCREEN = False  # Desactivado para usar tamaño fijo
WIN_W, WIN_H = 1200, 960  # Tamaño fijo ventana y captura

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands_detector = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

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

def detectar_gesto_ok(lm) -> bool:
    # lm es un objeto Landmarks de MediaPipe
    thumb_tip = lm.landmark[4]
    index_tip = lm.landmark[8]
    dist = ((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2) ** 0.5
    return dist < 0.05

def run(arduino: object | None = None, camera_index: int = 0) -> None:
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara para el modo QR")
        return

    # Fijar resolución de captura
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIN_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WIN_H)

    # Crear ventana tamaño fijo
    cv2.namedWindow(WINDOW_QR, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_QR, WIN_W, WIN_H)

    print("[ MODO QR ] Mostrar QR. Haz gesto OK para cambiar modo (espera 3s) | 'q' o ESC para salir")

    bloqueado = False
    ultimo_url: str | None = None
    ultimo_open = 0.0

    ok_gesture_start: float | None = None
    DELAY_OK = 3.0  # segundos de delay antes de cambio

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.resize(frame, (WIN_W, WIN_H))

        # Detectar manos y gesto OK
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultados = hands_detector.process(rgb)

        gesto_ok_detectado = False
        if resultados.multi_hand_landmarks:
            for lm in resultados.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)
                if detectar_gesto_ok(lm):
                    gesto_ok_detectado = True
                    break

        # Si gesto OK detectado, iniciar/revisar temporizador
        now = time.time()
        if gesto_ok_detectado:
            if ok_gesture_start is None:
                ok_gesture_start = now
            elif now - ok_gesture_start >= DELAY_OK:
                print("✅ Gesto OK mantenido 3s, cambiando modo...")
                break  # salir del modo QR para cambiar
            # Mostrar texto de cuenta regresiva para feedback
            tiempo_restante = int(DELAY_OK - (now - ok_gesture_start) + 1)
            cv2.putText(frame, f"Cambiando modo en: {tiempo_restante}s",
                        (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        else:
            ok_gesture_start = None

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
            if key in (27, ord("q")):
                sys.exit(0)
            continue
        else:
            if bloqueado:
                print("✅ Ventana con focus — escaneo reanudado")
                bloqueado = False

        # Escaneo QR solo si no bloqueado
        if not bloqueado:
            for qr in decode(frame):
                url = qr.data.decode()
                if url == ultimo_url and (now - ultimo_open) < 3:
                    continue
                print("QR:", url)
                ultimo_url, ultimo_open = url, now
                webbrowser.open(url)
                bloqueado = True
                break

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            sys.exit(0)

    cap.release()
    cv2.destroyWindow(WINDOW_QR)
