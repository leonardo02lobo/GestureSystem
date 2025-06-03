import cv2
import mediapipe as mp
import time
import sys
import platform # Importar para el uso en PositionController

# Importar tus clases de gestos
from Gestos.Chorme import ChromeController
from Gestos.Cerrar import CerrarController
from Gestos.Pinza import PinzaController
from Gestos.Position import PositionController # Asegúrate que este sea tu archivo modificado
from Manager.ChormeManager import AdministradorDePestanasChrome

def inicializar():
    mpManos = mp.solutions.hands
    # Configurar MediaPipe Hands: max_num_hands=1 es crucial para evitar confusión si se detectan dos manos
    manos = mpManos.Hands(max_num_hands=1, min_detection_confidence=0.7)
    mpDibujo = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)
    
    # Inicializar tus controladores existentes
    controladorChrome = ChromeController("chrome", False)
    controladorCerrar = CerrarController("cerrar", False)
    controladorPinza = PinzaController("pinza", False)
    
    # Inicializar el PositionController (ahora para el deslizamiento de escritorio)
    # Los argumentos posicionInicial y posicionFinal en el constructor original no son necesarios para este gesto.
    # Si tu clase base GestosController solo espera nombre y encendido, ajusta el constructor de PositionController.
    controladorDeslizamientoEscritorio = PositionController("deslizamiento_escritorio", True) # Lo encendemos por defecto
    
    administradorChrome = AdministradorDePestanasChrome()
    
    # Retornar todos los controladores y recursos necesarios
    return manos, mpDibujo, cap, controladorChrome, controladorCerrar, controladorPinza, controladorDeslizamientoEscritorio, administradorChrome, mpManos

def limpiar(cap, administradorChrome):
    administradorChrome.cerrarTodasLasPestanas()
    administradorChrome.detener()
    cap.release()
    cv2.destroyAllWindows()
    sys.exit(0)

def procesarGestos(landmarks, controladores, ultimoTiempoGesto, cooldown):
    tiempoActual = time.time()
    gestoDetectado = None # Almacena (controlador, nombre_gesto_string)
    
    for controlador in controladores:
        # Aquí, el controlador.detectarGestos ahora puede devolver el nombre del gesto
        # (ej. "deslizamiento_derecha", "pinza", etc.) o None.
        # Si el gesto ya se encarga de su propia acción (como el deslizamiento),
        # solo necesitamos su nombre para mostrarlo.
        gesto_nombre = controlador.detectarGestos(landmarks)
        if gesto_nombre:
            if (tiempoActual - ultimoTiempoGesto) > cooldown:
                gestoDetectado = (controlador, gesto_nombre)
                # No necesitamos `break` aquí si queremos que todos los controladores
                # tengan la oportunidad de detectar un gesto en el mismo frame.
                # Sin embargo, si un gesto es excluyente (solo se puede hacer uno a la vez),
                # el `break` es correcto. Para este caso, lo mantendremos para evitar
                # activaciones simultáneas de diferentes gestos que puedan solaparse.
                break 
    
    return gestoDetectado, tiempoActual

def ejecutarAccionGesto(controlador, gesto_nombre):
    # Solo ejecuta acciones que no son autocontenidas dentro del detector de gestos
    if isinstance(controlador, ChromeController) and gesto_nombre == "abrirChrome":
        controlador.abrirChrome()
    elif isinstance(controlador, PinzaController) and gesto_nombre == "pinza":
        controlador.abrirAdministradorDeArchivos()
    # Los gestos de PositionController (deslizamiento) ya manejan la acción internamente.
    # No es necesario agregar:
    # elif isinstance(controlador, PositionController) and (gesto_nombre == "deslizamiento_derecha" or gesto_nombre == "deslizamiento_izquierda"):
    #     pass # La acción ya fue ejecutada dentro de PositionController.detectarGestos

def mostrarInformacion(frame, nombreGesto, cooldownActivo):
    colorTexto = (0, 255, 0) if not cooldownActivo else (0, 0, 255)
    cv2.putText(frame, "Control de Gestos - Navegador", (50, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    if nombreGesto:
        cv2.putText(frame, f"Gesto: {nombreGesto}", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, colorTexto, 2)
    else:
        cv2.putText(frame, "Gesto: Ninguno", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)


def main():
    manos, mpDibujo, cap, controladorChrome, controladorCerrar, controladorPinza, controladorDeslizamientoEscritorio, administradorChrome, mpManos = inicializar()
    
    # Añadir el controlador de deslizamiento a la lista de controladores
    controladores = [controladorPinza, controladorChrome, controladorCerrar, controladorDeslizamientoEscritorio]
    
    COOLDOWN_GESTO = 5 # Cooldown global para evitar múltiples activaciones rápidas de *cualquier* gesto
    ultimoTiempoGesto = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1) # Voltear la imagen horizontalmente para un efecto espejo
            rgbFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resultados = manos.process(rgbFrame)
            gestoActual = None # Variable para mostrar el gesto detectado en pantalla
            cooldownActivo = (time.time() - ultimoTiempoGesto) <= COOLDOWN_GESTO

            if resultados.multi_hand_landmarks:
                for landmarks in resultados.multi_hand_landmarks:
                    mpDibujo.draw_landmarks(frame, landmarks, mpManos.HAND_CONNECTIONS)

                    # Procesar todos los controladores, el cooldown global se encarga de la pausa
                    infoGesto, tiempoDeteccion = procesarGestos(
                        landmarks, controladores, ultimoTiempoGesto, COOLDOWN_GESTO)

                    if infoGesto:
                        controlador, nombre_gesto_detectado = infoGesto
                        # ejecutarAccionGesto solo para los gestos que no se auto-ejecutan
                        ejecutarAccionGesto(controlador, nombre_gesto_detectado)
                        gestoActual = nombre_gesto_detectado # Almacenar el nombre para mostrar
                        ultimoTiempoGesto = tiempoDeteccion
                        cooldownActivo = False # Si hay un gesto, el cooldown se activa DESPUÉS de este momento


            mostrarInformacion(frame, gestoActual, cooldownActivo)
            cv2.imshow("Control por Gestos", frame)

            if cv2.waitKey(1) & 0xFF == ord('q') or \
               cv2.getWindowProperty("Control por Gestos", cv2.WND_PROP_VISIBLE) < 1:
                break

    finally:
        limpiar(cap, administradorChrome)

if __name__ == "__main__":
    main()