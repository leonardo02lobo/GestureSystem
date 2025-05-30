from GestosController import GestosController
import platform
import subprocess
import os

class PinzaController(GestosController):
    def __init__(self, nombre, encendido):
        super().__init__(nombre, encendido)
    
    def detectarGestos(self, hand_landmarks):
        try:
            landmarks = hand_landmarks.landmark
            
            if len(landmarks) < 21:
                return None
            
            punta_pulgar = landmarks[4]
            punta_indice = landmarks[8]
            distancia = ((punta_pulgar.x - punta_indice.x) ** 2 + 
                         (punta_pulgar.y - punta_indice.y) ** 2) ** 0.5
            
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