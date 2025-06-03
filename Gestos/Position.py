from GestosController import GestosController


class PositionController(GestosController):
    def __init__(self,nombre, encendido, posicionInicial, posicionFinal):
        super().__init__(nombre, encendido)
        self.posicionInicial = posicionInicial 
        self.posicionFinal = posicionFinal      
        self.posicionActual = posicionInicial 

    def detectarGestos(self, hand_landmarks):
        indice = hand_landmarks.landmark[8]
        print(indice.x, indice.y, indice.z)
        pass

    def move_to_position(self):
        # Lógica para mover de la posición actual a la posición final
        # Aquí puedes implementar la lógica de movimiento, por ejemplo, interpolación
        # Para simplificar, solo actualizaremos la posición actual a la final
        self.posicionActual = self.posicionFinal

    def execute_action(self):
        # Aquí puedes definir la acción a realizar al llegar a la posición final
        print(f"Acción ejecutada al llegar a la posición: {self.posicionActual}")
