import time
from GestosController import GestosController
import platform
import subprocess
import os

class ChormeController(GestosController):
    def __init__(self, nombre, encendido):
        super().__init__(nombre, encendido)
        self.ultimo_gesto_detectado = None
        self.ultimo_tiempo_deteccion = 0
        self.gesture_hold_threshold = 2  # segundos para mantener el gesto
        self.tiempo_espera = 0.5  # segundos de espera mínima
        self.gesture_start_time = 0

    def detectarGestos(self, hand_landmarks):
        try:
            landmarks = hand_landmarks.landmark
            
            if len(landmarks) < 21:
                return None
                
            punta_indice = landmarks[8]
            base_indice = landmarks[5]

            gesto_actual = None
            if punta_indice.y < base_indice.y:
                gesto_actual = "abrirChorme"
            
            # Si el gesto actual es diferente al último detectado, reiniciamos el temporizador
            if gesto_actual != self.ultimo_gesto_detectado:
                self.gesture_start_time = time.time()
                self.ultimo_tiempo_deteccion = time.time()
                self.ultimo_gesto_detectado = gesto_actual
                return None
            
            # Verificar si el gesto se ha mantenido el tiempo suficiente
            if (gesto_actual and 
                (time.time() - self.gesture_start_time) >= self.gesture_hold_threshold):
                return gesto_actual
            
            # Si ha pasado el tiempo de espera y el gesto se mantiene
            if (gesto_actual is not None and 
                (time.time() - self.ultimo_tiempo_deteccion) >= self.tiempo_espera):
                return gesto_actual
                
            return None
        except Exception as e:
            print(f"Error al detectar gestos: {str(e)}")
            return None

    def AbrirChrome(self):
        sistema = platform.system()
        try:
            if sistema == "Windows":
                subprocess.Popen(["start", "chrome"], shell=True)
            elif sistema == "Linux":
                desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
                
                # Intentar con el comando genérico primero
                try:
                    subprocess.Popen(["google-chrome"])
                except:
                    # Fallback para diferentes distribuciones
                    browsers = ["google-chrome", "chromium", "chrome"]
                    for browser in browsers:
                        try:
                            subprocess.Popen([browser])
                            break
                        except:
                            continue
            else:
                print(f"Sistema operativo no soportado: {sistema}")
                return False
        
            return True
        except Exception as e:
            print(f"Error al abrir Chrome: {e}")
            return False