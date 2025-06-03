import time
from GestosController import GestosController
import platform
import subprocess
import os

class PinzaController(GestosController):
    def __init__(self, nombre, encendido):
        super().__init__(nombre, encendido)
        self.ultimoGestoDetectado = None
        self.ultimoTiempoDeteccion = 0
        self.gestoSostenidoUmbral = 4
        self.distanciaMinimaPinza = 0.08 
        self.tiempoEspera = 0.5
    
    def detectarGestos(self, hand_landmarks):
        try:
            landmarks = hand_landmarks.landmark
            
            if len(landmarks) < 21:
                return None
            
            puntaPulgar = landmarks[4]
            puntaIndice = landmarks[8]
            distancia = ((puntaPulgar.x - puntaIndice.x) ** 2 + 
                         (puntaPulgar.y - puntaIndice.y) ** 2) ** 0.5
            
            gestoActual = None
            if distancia < 0.1:
                return "pinza"
        
            if gestoActual != self.ultimoGestoDetectado:
                self.ultimoTiempoDeteccion = time.time()
                self.ultimoGestoDetectado = gestoActual
                return None
            
            if (gestoActual and 
                (time.time() - self.gestoInicioTiempo) >= self.gestoSostenidoUmbral):
                return gestoActual
            
            if (gestoActual is not None and 
                (time.time() - self.ultimoTiempoDeteccion) >= self.tiempoEspera):
                return gestoActual
            if distancia < 0.1:
                return "pinza"
                
            return None
        except Exception as e:
            print(f"Error al detectar gestos: {str(e)}")
            return None
    
    def abrirAdministradorDeArchivos(self):
        sistema = platform.system()
        try:
            if sistema == "Windows":
                subprocess.Popen(["explorer"])
            elif sistema == "Linux":
                escritorio = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

                if "gnome" in escritorio:
                    subprocess.Popen(["nautilus","--new-window"])
                elif "kde" in escritorio:
                    subprocess.Popen(["dolphin"])
                elif "xfce" in escritorio:
                    subprocess.Popen(["thunar"])
                else:
                    subprocess.Popen(["xdg-open", os.path.expanduser("~")])
            else:
                print(f"Sistema operativo no soportado: {sistema}")
                return False
        
            return True
        except Exception as e:
            print(f"Error al abrir administrador de archivos: {e}")
            return False
