import cv2
import mediapipe as mp
import time
import sys
from Gestos.Chorme import ChromeController
from Gestos.Cerrar import CerrarController
from Gestos.Pinza import PinzaController
from Gestos.Position import PositionController
from Manager.ChormeManager import AdministradorDePestanasChrome

def inicializar():
    mpManos = mp.solutions.hands
    manos = mpManos.Hands(max_num_hands=1, min_detection_confidence=0.7)
    mpDibujo = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)
    
    controladorChrome = ChromeController("chrome", False)
    controladorCerrar = CerrarController("cerrar", False)
    controladorPinza = PinzaController("pinza", False)
    
    administradorChrome = AdministradorDePestanasChrome()
    
    return manos, mpDibujo, cap, controladorChrome, controladorCerrar, controladorPinza, administradorChrome, mpManos

def limpiar(cap, administradorChrome):
    administradorChrome.cerrarTodasLasPestanas()
    administradorChrome.detener()
    cap.release()
    cv2.destroyAllWindows()
    sys.exit(0)

def procesarGestos(landmarks, controladores, ultimoTiempoGesto, cooldown):
    tiempoActual = time.time()
    gestoDetectado = None
    
    for controlador in controladores:
        gesto = controlador.detectarGestos(landmarks)
        if gesto:
            if (tiempoActual - ultimoTiempoGesto) > cooldown:
                gestoDetectado = (controlador, gesto)
            break
    
    return gestoDetectado, tiempoActual

def ejecutarAccionGesto(controlador, gesto):
    if isinstance(controlador, ChromeController) and gesto == "abrirChrome":
        controlador.abrirChrome()
    elif isinstance(controlador, PinzaController) and gesto == "pinza":
        controlador.abrirAdministradorDeArchivos()

def mostrarInformacion(frame, nombreGesto, cooldownActivo):
    colorTexto = (0, 255, 0) if not cooldownActivo else (0, 0, 255)
    cv2.putText(frame, "Control de Gestos - Navegador", (50, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    if nombreGesto:
        cv2.putText(frame, f"Gesto: {nombreGesto}", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, colorTexto, 2)

def main():
    manos, mpDibujo, cap, controladorChrome, controladorCerrar, controladorPinza, administradorChrome, mpManos = inicializar()
    controladores = [controladorPinza, controladorChrome, controladorCerrar]
    COOLDOWN_GESTO = 5
    ultimoTiempoGesto = 0

    posicionInicio = (0, 100) 
    posicionFin = (100, 100) 
    controladorPosicion = PositionController("volumen",False,posicionInicio, posicionFin)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            rgbFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resultados = manos.process(rgbFrame)
            gestoActual = None
            cooldownActivo = (time.time() - ultimoTiempoGesto) <= COOLDOWN_GESTO

            if resultados.multi_hand_landmarks:
                for landmarks in resultados.multi_hand_landmarks:
                    mpDibujo.draw_landmarks(frame, landmarks, mpManos.HAND_CONNECTIONS)

                    controladorPosicion.detectarGestos(landmarks)
                    infoGesto, tiempoDeteccion = procesarGestos(
                        landmarks, controladores, ultimoTiempoGesto, COOLDOWN_GESTO)

                    if infoGesto:
                        controlador, gesto = infoGesto
                        ejecutarAccionGesto(controlador, gesto)
                        gestoActual = gesto
                        ultimoTiempoGesto = tiempoDeteccion
                        cooldownActivo = False

                        controladorPosicion.move_to_position()
                        controladorPosicion.execute_action()

            mostrarInformacion(frame, gestoActual, cooldownActivo)
            cv2.imshow("Control por Gestos", frame)

            if cv2.waitKey(1) & 0xFF == ord('q') or \
               cv2.getWindowProperty("Control por Gestos", cv2.WND_PROP_VISIBLE) < 1:
                break

    finally:
        limpiar(cap, administradorChrome)

if __name__ == "__main__":
    main()