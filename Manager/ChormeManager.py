import subprocess
import threading
import time
from typing import List

class AdministradorDePestanasChrome:
    def __init__(self):
        self.pestanas: List[subprocess.Popen] = []
        self.hiloMonitor = threading.Thread(target=self._monitorPestanas, daemon=True)
        self.ejecutando = True
        self.hiloMonitor.start()
    
    def abrirPestana(self, url: str = None):
        cmd = ["google-chrome"]
        if url:
            cmd.append(url)
        nuevaPestana = subprocess.Popen(cmd)
        self.pestanas.append(nuevaPestana)
        return nuevaPestana
    
    def cerrarTodasLasPestanas(self):
        for pestana in self.pestanas:
            try:
                pestana.terminate()
            except:
                pass
        self.pestanas.clear()
    
    def _monitorPestanas(self):
        while self.ejecutando:
            for i, pestana in enumerate(self.pestanas[:]):
                if pestana.poll() is not None:  
                    self.pestanas.pop(i)
                    print(f"Pestaña cerrada, quedan {len(self.pestanas)} pestañas abiertas")
            time.sleep(1) 
    
    def detener(self):
        self.ejecutando = False
        self.hiloMonitor.join()