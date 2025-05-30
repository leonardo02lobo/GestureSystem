from Gestos.Chorme import ChormeController
from Gestos.Cerrar import CerrarController
from Gestos.Pinza import PinzaController
from Manager.ChromeManager import ChromeTabManager
import cv2
import mediapipe as mp
import time
import sys

# Configuración de MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

# Controladores
chorme = ChormeController("chorme", False)
cerrar = CerrarController("cerrar", False)
pinza = PinzaController("pinza",False)

# Configuración de tiempos
ultimo_gesto_time = 0
cooldown_gesto = 5  # Segundos entre ejecuciones del mismo gesto
ultimo_gesto_time = 0
cooldown_gesto = 2  # Segundos entre ejecuciones

# Inicializar el administrador de pestañas
chrome_manager = ChromeTabManager()

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
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                if pinza.detectarGestos(hand_landmarks) == "pinza":
                    tiempo_actual = time.time()
                    if (tiempo_actual - ultimo_gesto_time) > cooldown_gesto:
                        if pinza.AbrirAdministradorDeArchivos():
                            print("Administrador de archivos abierto")
                            pinza.encendido = True
                            ultimo_gesto_time = tiempo_actual
                            cv2.putText(frame, "Administrador abierto", (50, 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    break
                elif chorme.detectarGestos(hand_landmarks) == "abrirChorme":
                    tiempo_actual = time.time()
                    if (tiempo_actual - ultimo_gesto_time) > cooldown_gesto:
                        chrome_manager.open_tab()
                        chorme.encendido = True
                        ultimo_gesto_time = tiempo_actual
                        cv2.putText(frame, "Chorme", (50, 50), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    break

                
                # if cerrar.detectarGestos(hand_landmarks) == "cerrar":
                #     chrome_manager.close_all_tabs()
                #     time.sleep(1)
                #     cleanup()
        
        cv2.putText(frame, "Navegador", (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        cv2.imshow("Control por Gestos", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty("Control por Gestos", cv2.WND_PROP_VISIBLE) < 1:
            break

finally:
    cleanup()