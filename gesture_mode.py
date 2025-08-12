from __future__ import annotations

import cv2
import time
import sys
import serial
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

GESTURE_DELAY = 1.0
HAND_TIMEOUT = 2.0

current_led_state = {"8": False, "3": False, "4": False}

# ---- Config de ventana ----
WINDOW_TITLE = "Control por Gestos"
FULLSCREEN = False  # Desactivado para ventana tamaño fijo
WIN_W, WIN_H = 960, 960  # Tamaño fijo ventana y captura

DELAY_OK = 3.0  # Segundos que debe mantenerse el gesto OK para activar cambio

def control_led(arduino: serial.Serial, estado: str, pin: str = "") -> None:
    """Enciende (*estado == 'on'*) o apaga (*estado == 'off'*) LEDs por pin."""
    global current_led_state
    if estado == "on" and pin and not current_led_state.get(pin, False):
        arduino.write(pin.encode())
        current_led_state[pin] = True
        print(f"💡 LED {pin} ON")
    elif estado == "off":
        arduino.write(b"0")
        current_led_state = {"8": False, "3": False, "4": False}
        print("🔌 LEDs OFF")

def detectar_posicion_mano(lm, w: int, h: int) -> str | None:
    """Devuelve 'izquierda', 'derecha' o 'arriba' según la posición de la muñeca."""
    wrist = lm.landmark[0]
    x_px, y_px = wrist.x * w, wrist.y * h
    if y_px < h * 0.25:
        return "arriba"
    if x_px < w * 0.33:
        return "izquierda"
    if x_px > w * 0.66:
        return "derecha"
    return None

def detectar_gesto_ok(lm) -> bool:
    thumb_tip = lm.landmark[4]
    index_tip = lm.landmark[8]
    dist = ((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2) ** 0.5
    return dist < 0.05

def run(arduino: serial.Serial, camera_index: int = 0) -> None:
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara para Gestos")
        return

    # Fijar resolución de captura
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIN_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WIN_H)

    # Crear ventana tamaño fijo
    cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_TITLE, WIN_W, WIN_H)

    print("[ MODO GESTOS ] Cambia modo haciendo gesto OK (mantener 3s) | 'q' o ESC para salir")

    last_position_time = 0.0
    last_hand_seen_time = 0.0
    ok_gesture_start: float | None = None

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            # Forzar tamaño del frame para mantener 960x960
            frame = cv2.resize(frame, (WIN_W, WIN_H))

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]
            t = time.time()

            resultados = hands.process(rgb)
            hand_present = False

            gesto_ok_detectado = False

            if resultados.multi_hand_landmarks:
                hand_present = True
                last_hand_seen_time = t
                for lm in resultados.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

                    # Detectar gesto OK para cambio modo
                    if detectar_gesto_ok(lm):
                        gesto_ok_detectado = True
                        control_led(arduino, "on", "4")
                        cv2.putText(frame, "👍 Gesto OK", (10, 90),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    else:
                        # Opcional: apagar LED 4 si no hay gesto OK en esta mano
                        pass

                    # Posición de muñeca rate-limited
                    if t - last_position_time > GESTURE_DELAY:
                        pos = detectar_posicion_mano(lm, w, h)
                        if pos == "izquierda":
                            control_led(arduino, "on", "8")
                            last_position_time = t
                        elif pos == "derecha":
                            control_led(arduino, "on", "3")
                            last_position_time = t
                        elif pos == "arriba":
                            control_led(arduino, "off")
                            last_position_time = t

            # Control apagado LED 4 tras timeout si mano desaparece
            if not hand_present and current_led_state.get("4", False):
                if t - last_hand_seen_time > HAND_TIMEOUT:
                    control_led(arduino, "off")

            # Manejo del temporizador para gesto OK mantenido
            if gesto_ok_detectado:
                if ok_gesture_start is None:
                    ok_gesture_start = t
                else:
                    tiempo_mantener = t - ok_gesture_start
                    tiempo_restante = int(DELAY_OK - tiempo_mantener + 1)
                    cv2.putText(frame, f"Cambiar modo en: {tiempo_restante}s",
                                (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    if tiempo_mantener >= DELAY_OK:
                        print("✅ Gesto OK mantenido, cambiando modo...")
                        break
            else:
                ok_gesture_start = None

            # HUD
            cv2.putText(frame, "C O N T R O L   P O R   G E S T O S", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 255), 2)
            cv2.putText(frame, "q/ESC: salir", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 1)

            cv2.imshow(WINDOW_TITLE, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                sys.exit(0)

    finally:
        cap.release()
        cv2.destroyAllWindows()
