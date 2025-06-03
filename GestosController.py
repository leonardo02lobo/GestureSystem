import psutil

class GestosController:
    def __init__(self, nombre, encendido):
        self.nombre = nombre
        self.encendido = encendido
        self.psutil = psutil
    
    def estaActivo(self):
        for proceso in self.psutil.process_iter(['name']):
            if proceso.info['name'] and 'chrome' in proceso.info['name'].lower():
                return True
        return False

    def detectarGestos(self, landmarks):
        pass
