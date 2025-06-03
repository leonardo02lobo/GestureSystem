import cv2
import mediapipe as mp
import time
import sys
from Gestos.Chorme import ChormeController
from Gestos.Cerrar import CerrarController
from Gestos.Pinza import PinzaController
from Manager.ChormeManager import ChromeTabManager

# Configuración inicial
def initialize():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    mp_draw = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)
    
    # Controladores
    chrome_controller = ChormeController("chrome", False)
    close_controller = CerrarController("cerrar", False)
    pinch_controller = PinzaController("pinza", False)
    
    # Administrador de Chrome
    chrome_manager = ChromeTabManager()
    
    return hands, mp_draw, cap, chrome_controller, close_controller, pinch_controller, chrome_manager,mp_hands

# Limpieza de recursos
def cleanup(cap, chrome_manager):
    chrome_manager.close_all_tabs()
    chrome_manager.stop()
    cap.release()
    cv2.destroyAllWindows()
    sys.exit(0)

# Procesamiento de gestos
def process_gestures(landmarks, controllers, last_gesture_time, cooldown):
    current_time = time.time()
    gesture_detected = None
    
    # Verificar cada controlador
    for controller in controllers:
        gesture = controller.detectarGestos(landmarks)
        if gesture:
            if (current_time - last_gesture_time) > cooldown:
                gesture_detected = (controller, gesture)
            break
    
    return gesture_detected, current_time

# Ejecutar acción correspondiente al gesto
def execute_gesture_action(controller, gesture):
    if isinstance(controller, ChormeController) and gesture == "abrirChorme":
        controller.AbrirChrome()
    elif isinstance(controller, PinzaController) and gesture == "pinza":
        controller.AbrirAdministradorDeArchivos()

# Mostrar información en pantalla
def display_info(frame, gesture_name, cooldown_active):
    text_color = (0, 255, 0) if not cooldown_active else (0, 0, 255)
    cv2.putText(frame, "Control de Gestos - Navegador", (50, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    if gesture_name:
        cv2.putText(frame, f"Gesto: {gesture_name}", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)

# Main
def main():
    # Inicialización
    hands, mp_draw, cap, chrome_controller, close_controller, pinch_controller, chrome_manager,mp_hands= initialize()
    controllers = [pinch_controller, chrome_controller, close_controller]
    GESTURE_COOLDOWN = 5
    last_gesture_time = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Procesamiento de imagen
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)
            current_gesture = None
            cooldown_active = (time.time() - last_gesture_time) <= GESTURE_COOLDOWN

            if results.multi_hand_landmarks:
                for landmarks in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # Detección de gestos
                    gesture_info, detection_time = process_gestures(
                        landmarks, controllers, last_gesture_time, GESTURE_COOLDOWN)
                    
                    if gesture_info:
                        controller, gesture = gesture_info
                        execute_gesture_action(controller, gesture)
                        current_gesture = gesture
                        last_gesture_time = detection_time
                        cooldown_active = False

            # Mostrar información
            display_info(frame, current_gesture, cooldown_active)
            cv2.imshow("Control por Gestos", frame)
            
            # Salir con 'q' o al cerrar la ventana
            if cv2.waitKey(1) & 0xFF == ord('q') or \
               cv2.getWindowProperty("Control por Gestos", cv2.WND_PROP_VISIBLE) < 1:
                break

    finally:
        cleanup(cap, chrome_manager)

if __name__ == "__main__":
    main()