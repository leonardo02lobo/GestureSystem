from GestosController import GestosController

class CerrarController(GestosController):
    def __init__(self, nombre, encendido):
        super().__init__(nombre, encendido)

    def detectarGestos(self, hand_landmarks):
        try:
            landmarks = hand_landmarks.landmark
            
            if len(landmarks) < 21:
                return None
                
            puntaIndice = landmarks[20]
            baseIndice = landmarks[17]
            distancia = ((baseIndice.x - puntaIndice.x) ** 2 + 
                         (baseIndice.y - puntaIndice.y) ** 2) ** 0.5

            if puntaIndice.y < baseIndice.y:
                return "cerrar"
                
            return None
        except Exception as e:
            print(f"Error al detectar gestos: {str(e)}")
            return None
