import time
from GestosController import GestosController

class ChormeController(GestosController):
    def __init__(self,nombre,encendido):
        super().__init__(nombre,encendido)
<<<<<<< HEAD
        self.ultimo_gesto_detectado = None
        self.ultimo_tiempo_deteccion = 0
        self.gesture_hold_threshold = 4
        self.min_pinch_distance = 0.08 
        self.tiempo_espera = 0.5
=======
>>>>>>> 682df73c5084299098876d88a46c4cb959dcf706

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