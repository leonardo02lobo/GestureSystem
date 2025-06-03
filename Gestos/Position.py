class PositionController:
    def __init__(self, posicionInicial, posicionFinal):
        self.posicionInicial = posicionInicial 
        self.posicionFinal = posicionFinal      
        self.posicionActual = posicionInicial 

    def move_to_position(self):
        # Lógica para mover de la posición actual a la posición final
        # Aquí puedes implementar la lógica de movimiento, por ejemplo, interpolación
        # Para simplificar, solo actualizaremos la posición actual a la final
        self.posicionActual = self.posicionFinal

    def execute_action(self):
        # Aquí puedes definir la acción a realizar al llegar a la posición final
        print(f"Acción ejecutada al llegar a la posición: {self.posicionActual}")
