import time
from GestosController import GestosController
import platform
import subprocess
import os

class ChromeController(GestosController):
    def __init__(self, nombre, encendido):
        super().__init__(nombre, encendido)
        self.ultimoGestoDetectado = None
        self.ultimoTiempoDeteccion = 0
        self.gestoSostenidoUmbral = 4  # segundos para mantener el gesto
        self.tiempoEspera = 0.5  # segundos de espera mínima
        self.gestoInicioTiempo = 0

    def detectarGestos(self, hand_landmarks):
        try:
            landmarks = hand_landmarks.landmark
            
            if len(landmarks) < 21:
                return None
                
            puntaIndice = landmarks[8]
            baseIndice = landmarks[5]

            gestoActual = None
            if puntaIndice.y < baseIndice.y:
                gestoActual = "abrirChrome"
            
            # Si el gesto actual es diferente al último detectado, reiniciamos el temporizador
            if gestoActual != self.ultimoGestoDetectado:
                self.gestoInicioTiempo = time.time()
                self.ultimoTiempoDeteccion = time.time()
                self.ultimoGestoDetectado = gestoActual
                return None
            
            # Verificar si el gesto se ha mantenido el tiempo suficiente
            if (gestoActual and 
                (time.time() - self.gestoInicioTiempo) >= self.gestoSostenidoUmbral):
                return gestoActual
            
            # Si ha pasado el tiempo de espera y el gesto se mantiene
            if (gestoActual is not None and 
                (time.time() - self.ultimoTiempoDeteccion) >= self.tiempoEspera):
                return gestoActual
                
            return None
        except Exception as e:
            print(f"Error al detectar gestos: {str(e)}")
            return None

    def abrirChrome(self):
        sistema = platform.system()
        try:
            if sistema == "Windows":
                subprocess.Popen("start chrome", shell=True)
            elif sistema == "Linux":
                escritorio = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
                
                try:
                    subprocess.Popen(["google-chrome"])
                except:
                    navegadores = ["google-chrome", "chromium", "chrome"]
                    for navegador in navegadores:
                        try:
                            subprocess.Popen([navegador])
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
