from GestosController import GestosController

class CerrarController(GestosController):
    def __init__(self,nombre,encendido):
        super().__init__(nombre,encendido)

    def detectarGestos(self,hand_landmarks):
        try:
            landmarks = hand_landmarks.landmark
            
            if len(landmarks) < 21:
                return None
                
            punta_indice = landmarks[20]
            base_indice = landmarks[17]
            distancia = ((base_indice.x - punta_indice.x) ** 2 + 
                         (base_indice.y - punta_indice.y) ** 2) ** 0.5

            if punta_indice.y < base_indice.y:
                return "cerrar"
                
            return None
        except Exception as e:
            print(f"Error al detectar gestos: {str(e)}")
            return None