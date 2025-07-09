import cv2
import mediapipe as mp
import time
import sys
from Gestos.Chorme import ChromeController
from Gestos.Pinza import PinzaController
from Manager.ChormeManager import AdministradorDePestanasChrome

# Inicialización de MediaPipe
mp_hands = mp.solutions.hands
mp_face_mesh = mp.solutions.face_mesh
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

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

def detectar_distancia(landmarks_cara, frame_height):
    frente = landmarks_cara.landmark[10].y * frame_height
    barbilla = landmarks_cara.landmark[152].y * frame_height
    return abs(frente - barbilla) > frame_height * 0.4

def main():
    cap, controladorChrome, controladorPinza, administradorChrome = inicializar()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_height, frame_width = frame.shape[:2]

            # Procesar cara primero
            resultados_cara = face_mesh.process(frame_rgb)
            if resultados_cara.multi_face_landmarks:
                for landmarks_cara in resultados_cara.multi_face_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, landmarks_cara, mp_face_mesh.FACEMESH_CONTOURS)
                    
                    # Detección de distancia
                    if detectar_distancia(landmarks_cara, frame_height):
                        print(">>> ¡Demasiado cerca del monitor! Encender luz roja")
                    
                    # Detección de movimientos de cabeza
                    movimiento = detectar_movimiento_cabeza(landmarks_cara.landmark, frame_width)
                    if movimiento == "izquierda":
                        print(">>> Movimiento a la izquierda: Encender luz 1")
                    elif movimiento == "derecha":
                        print(">>> Movimiento a la derecha: Encender luz 2")
                    elif movimiento == "arriba":
                        print(">>> Cabeza elevada: Apagar todas las luces")

            # Procesar manos
            resultados_manos = hands.process(frame_rgb)
            if resultados_manos.multi_hand_landmarks:
                for landmarks_mano in resultados_manos.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, landmarks_mano, mp_hands.HAND_CONNECTIONS)
                    
                    gesto = detectar_gesto_mano(landmarks_mano)
                    if gesto == "ok":
                        print(">>> Gesto 'OK' detectado: Encender luz RGB")
                    # Aquí puedes añadir más gestos como palma abierta

            cv2.imshow("Control por Gestos", frame)
            # Verificar si el usuario cerró la ventana (X) o presionó 'q'
            if (cv2.waitKey(1) & 0xFF == ord('q')) or \
               (cv2.getWindowProperty("Control por Gestos", cv2.WND_PROP_VISIBLE) < 1):
                break  # Salir del bucle si se cierra la ventana o se presiona 'q'

    finally:
        limpiar(cap, administradorChrome)

if __name__ == "__main__":
    main()