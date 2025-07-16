import cv2
import mediapipe as mp
import time
import sys
import serial
from Gestos.Chorme import ChromeController
from Gestos.Pinza import PinzaController
from Manager.ChormeManager import AdministradorDePestanasChrome

# Inicialización de MediaPipe
mp_hands = mp.solutions.hands
mp_face_mesh = mp.solutions.face_mesh
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Configuración serial para Arduino
try:
    arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    time.sleep(2)
    arduino.reset_input_buffer()
except serial.SerialException as e:
    print(f"Error al abrir el puerto serial: {e}")
    sys.exit(1)

# Variables globales para control
last_gesture_time = 0
GESTURE_DELAY = 1.0  # 1 segundo de delay para confirmar gesto
current_led_state = {'8': False, '3': False, '4': False}
last_hand_detection_time = 0
HAND_TIMEOUT = 2.0  # 2 segundos sin detectar mano para apagar LEDs

def control_led(estado, pin=''):
    global current_led_state
    if estado == 'on' and not current_led_state[pin]:
        arduino.write(pin.encode())
        current_led_state[pin] = True
        print(f">>> LED {pin} encendido")
    elif estado == 'off':
        arduino.write(b'0')
        current_led_state = {'8': False, '3': False, '4': False}
        print(">>> LEDs apagados")

def apagar_todas():
    arduino.write(b'0')
    global current_led_state
    current_led_state = {'8': False, '3': False, '4': False}

def inicializar():
    cap = cv2.VideoCapture(0)
    controladorChrome = ChromeController("chrome", False)
    controladorPinza = PinzaController("pinza", False)
    administradorChrome = AdministradorDePestanasChrome()
    return cap, controladorChrome, controladorPinza, administradorChrome

def limpiar(cap, administradorChrome):
    administradorChrome.cerrarTodasLasPestanas()
    administradorChrome.detener()
    cap.release()
    cv2.destroyAllWindows()
    sys.exit(0)

def detectar_movimiento_cabeza(landmarks_cara, frame_width):
    nose_landmark = landmarks_cara[1]  # Landmark de la nariz
    nose_x = nose_landmark.x * frame_width

    if nose_x < frame_width * 0.4:
        return "izquierda"
    elif nose_x > frame_width * 0.6:
        return "derecha"
    elif landmarks_cara[10].y < 0.2:  # Punto de la frente
        return "arriba"
    return None

def detectar_gesto_mano(landmarks_mano):
    thumb_tip = landmarks_mano.landmark[4]
    index_tip = landmarks_mano.landmark[8]
    distancia = ((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)**0.5
    return "ok" if distancia < 0.05 else None

def detectar_distancia(landmarks_cara, frame_height, frame):
    frente = landmarks_cara.landmark[10].y * frame_height
    barbilla = landmarks_cara.landmark[152].y * frame_height
    distancia = abs(frente - barbilla)
    
    # Mostrar advertencia si está muy cerca
    if distancia > frame_height * 0.4:
        cv2.putText(frame, "DEMASIADO CERCA!", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return True
    return False

def main():
    global last_gesture_time, last_hand_detection_time
    cap, controladorChrome, controladorPinza, administradorChrome = inicializar()
    
    try:
        hand_detected = False
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_height, frame_width = frame.shape[:2]
            current_time = time.time()

            # Procesar cara
            resultados_cara = face_mesh.process(frame_rgb)
            if resultados_cara.multi_face_landmarks:
                for landmarks_cara in resultados_cara.multi_face_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, landmarks_cara, mp_face_mesh.FACEMESH_CONTOURS)
                    
                    # Detección de distancia (solo muestra advertencia)
                    # Dentro del bucle principal, donde procesas la cara
                    if detectar_distancia(landmarks_cara, frame_height, frame):
                        control_led('off')
                        last_gesture_time = current_time
                    
                    # Detección de gestos con delay
                    if current_time - last_gesture_time >= GESTURE_DELAY:
                        movimiento = detectar_movimiento_cabeza(landmarks_cara.landmark, frame_width)
                        
                        if movimiento == "izquierda":
                            control_led('on', '8')
                            last_gesture_time = current_time
                        elif movimiento == "derecha":
                            control_led('on', '3')
                            last_gesture_time = current_time
                        elif movimiento == "arriba":
                            control_led('off')
                            last_gesture_time = current_time

            # Procesar manos
            hand_currently_detected = False
            resultados_manos = hands.process(frame_rgb)
            if resultados_manos.multi_hand_landmarks:
                hand_currently_detected = True
                last_hand_detection_time = current_time
                
                for landmarks_mano in resultados_manos.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, landmarks_mano, mp_hands.HAND_CONNECTIONS)
                    
                    gesto = detectar_gesto_mano(landmarks_mano)
                    if gesto == "ok":
                        control_led('on', '4')
                        print(">>> Gesto 'OK' detectado")
            
            # Apagar LEDs si no se detecta mano por cierto tiempo
            if not hand_currently_detected and current_led_state['4']:
                if current_time - last_hand_detection_time > HAND_TIMEOUT:
                    control_led('off')

            # Mostrar información de estado
            cv2.putText(frame, f"LED 8: {'ON' if current_led_state['8'] else 'OFF'}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"LED 3: {'ON' if current_led_state['3'] else 'OFF'}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"LED 4: {'ON' if current_led_state['4'] else 'OFF'}", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.imshow("Control por Gestos", frame)
            if (cv2.waitKey(1) & 0xFF == ord('q')) or \
               (cv2.getWindowProperty("Control por Gestos", cv2.WND_PROP_VISIBLE) < 1):
                break

    finally:
        apagar_todas()
        limpiar(cap, administradorChrome)
        arduino.close()

if __name__ == "__main__":
    main()