# =========================
# gesture_mode.py
# =========================
"""Control de LEDs mediante gestos de **mano** (sin usar la cara).

Gestos reconocidos y su acción:
- Mano en el tercio IZQUIERDO de la pantalla  → LED 8 ON
- Mano en el tercio DERECHO de la pantalla   → LED 3 ON
- Mano en el tercio SUPERIOR de la pantalla  → Apagar LEDs (equivalente a "arriba")
- Gesto "OK" (pulgar–índice juntos)          → LED 4 ON

Mantiene la lógica de tiempo de espera para apagar LED 4 si la mano desaparece.
"""

from __future__ import annotations

import cv2
import time
import sys
import serial
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

GESTURE_DELAY = 1.0  # s entre gestos de posición de mano
HAND_TIMEOUT = 2.0   # s para apagar LED 4 cuando desaparece la mano

current_led_state = {"8": False, "3": False, "4": False}

# ----------------------------------------------------------------------------
# Funciones utilitarias
# ----------------------------------------------------------------------------

def control_led(arduino: serial.Serial, estado: str, pin: str = "") -> None:
    """Enciende (*estado == 'on'*) o apaga (*estado == 'off'*) LEDs por pin."""
    global current_led_state
    if estado == "on" and pin and not current_led_state[pin]:
        arduino.write(pin.encode())
        current_led_state[pin] = True
        print(f"💡 LED {pin} ON")
    elif estado == "off":
        arduino.write(b"0")
        current_led_state = {"8": False, "3": False, "4": False}
        print("🔌 LEDs OFF")


def detectar_posicion_mano(lm, w: int, h: int) -> str | None:
    """Devuelve 'izquierda', 'derecha' o 'arriba' según la posición de la muñeca."""
    wrist = lm.landmark[0]  # Muñeca
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

# ----------------------------------------------------------------------------
# Bucle principal
# ----------------------------------------------------------------------------

def run(arduino: serial.Serial, camera_index: int = 0) -> None:
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara para Gestos")
        return

    print("[ MODO GESTOS ] Presiona 'k' para cambiar de modo | 'q' o ESC para salir")

    last_position_time = 0.0
    last_hand_seen_time = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = frame.shape[:2]
        t = time.time()

        resultados = hands.process(rgb)
        hand_present = False
        if resultados.multi_hand_landmarks:
            hand_present = True
            last_hand_seen_time = t
            for lm in resultados.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

                # ---- Gesto OK (LED 4) ----
                if detectar_gesto_ok(lm):
                    control_led(arduino, "on", "4")
                    print("👍 Gesto OK detectado")

                # ---- Posición de la mano (LED 8 / LED 3 / OFF) ----
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

        # ---- Apagado automático LED 4 ----
        if not hand_present and current_led_state["4"]:
            if t - last_hand_seen_time > HAND_TIMEOUT:
                control_led(arduino, "off")

        cv2.imshow("Control por Gestos", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("k"):
            break  # Cambiar de modo
        if key in (27, ord("q")):
            sys.exit(0)

    cap.release()
    cv2.destroyAllWindows()
