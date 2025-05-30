import time
from GestosController import GestosController

class ChormeController(GestosController):
    def __init__(self,nombre,encendido):
        super().__init__(nombre,encendido)

    def detectarGestos(self,hand_landmarks):
        try:
            landmarks = hand_landmarks.landmark
            
            if len(landmarks) < 21:
                return None
                
            punta_indice = landmarks[8]
            base_indice = landmarks[5]

            if punta_indice.y < base_indice.y:
                return "abrirChorme"
                
            return None
        except Exception as e:
            print(f"Error al detectar gestos: {str(e)}")
            return None