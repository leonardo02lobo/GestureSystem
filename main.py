import cv2
import mediapipe as mp
import time
import sys
from Gestos.Chorme import ChormeController
from Gestos.Cerrar import CerrarController
from Gestos.Pinza import PinzaController
from Manager.ChromeManager import ChromeTabManager

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

cap = cv2.VideoCapture(0)

chrome_controller = ChormeController("chrome", False)
close_controller = CerrarController("cerrar", False)
pinch_controller = PinzaController("pinza", False)

chrome_manager = ChromeTabManager()

GESTURE_COOLDOWN = 5  # segundos
last_gesture_time = 0

def cleanup():
    chrome_manager.close_all_tabs()
    chrome_manager.stop()
    cap.release()
    cv2.destroyAllWindows()
    sys.exit(0)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)

                current_time = time.time()
                can_trigger = (current_time - last_gesture_time) > GESTURE_COOLDOWN

                if pinch_controller.detectarGestos(landmarks) == "pinza" and can_trigger:
                    if pinch_controller.AbrirAdministradorDeArchivos():
                        print("Administrador de archivos abierto")
                        pinch_controller.encendido = True
                        last_gesture_time = current_time
                        cv2.putText(frame, "Administrador abierto", (50, 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    break

                elif chrome_controller.detectarGestos(landmarks) == "abrirChorme" and can_trigger:
                    chrome_manager.open_tab()
                    chrome_controller.encendido = True
                    last_gesture_time = current_time
                    cv2.putText(frame, "Chrome abierto", (50, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    break

                # Si en el futuro quieres usar el gesto de cerrar, descomenta y adapta:
                # elif close_controller.detectarGestos(landmarks) == "cerrar":
                #     chrome_manager.close_all_tabs()
                #     time.sleep(1)
                #     cleanup()

        cv2.putText(frame, "Control de Gestos - Navegador", (50, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow("Control por Gestos", frame)

        if cv2.waitKey(1) & 0xFF == ord('q') or \
           cv2.getWindowProperty("Control por Gestos", cv2.WND_PROP_VISIBLE) < 1:
            break

finally:
    cleanup()
