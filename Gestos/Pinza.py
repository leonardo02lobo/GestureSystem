import time
import GestosController
import platform
import subprocess
import os

class PinzaController(GestosController):
    def __init__(self, nombre, encendido):
        super().__init__(nombre, encendido)
        self.ultimo_gesto_detectado = None
        self.ultimo_tiempo_deteccion = 0
        self.gesture_hold_threshold = 4
        self.min_pinch_distance = 0.08 
        self.tiempo_espera = 0.5
    
    def detectarGestos(self, hand_landmarks):
        try:
            landmarks = hand_landmarks.landmark
            
            if len(landmarks) < 21:
                return None
            
            punta_pulgar = landmarks[4]
            punta_indice = landmarks[8]
            distancia = ((punta_pulgar.x - punta_indice.x) ** 2 + 
                         (punta_pulgar.y - punta_indice.y) ** 2) ** 0.5
            
            gesto_actual = None
            if distancia < 0.1:
                return "pinza"
        
            # Si el gesto actual es diferente al último detectado, reiniciamos el temporizador
            if gesto_actual != self.ultimo_gesto_detectado:
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
            if distancia < 0.1:
                return "pinza"
                
            return None
        except Exception as e:
            print(f"Error al detectar gestos: {str(e)}")
            return None
    
    def AbrirAdministradorDeArchivos(self):
        sistema = platform.system()
        try:
            if sistema == "Windows":
                subprocess.Popen(["explorer"])
            elif sistema == "Linux":
                desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

                if "gnome" in desktop:
                    subprocess.Popen(["nautilus","--new-window"])
                elif "kde" in desktop:
                    subprocess.Popen(["dolphin"])
                elif "xfce" in desktop:
                    subprocess.Popen(["thunar"])
                else:
                    subprocess.Popen(["xdg-open",os.path.expanduser("~")])
            else:
                print(f"Sistema operativo no soportado: {sistema}")
                return False
        
            return True
        except Exception as e:
            print(f"Error al abrir administrador de archivos: {e}")
            return False