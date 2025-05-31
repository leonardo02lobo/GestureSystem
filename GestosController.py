import psutil
class GestosController:
    def __init__(self,nombre,encendido):
        self.nombre = nombre
        self.encendido = encendido
        self.psutil = psutil
    
    def EstaActivo(self):
        for proceso in self.psutil.process_iter(['name']):
            if 'chrome' in proceso.info['name'].lower():
                return True
        return False

    def detectarGestos(landmarks):
        pass