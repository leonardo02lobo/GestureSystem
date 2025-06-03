import subprocess
import threading
import time
from typing import List


class ChromeTabManager:
    def __init__(self):
        self.tabs: List[subprocess.Popen] = []
        self.monitor_thread = threading.Thread(target=self._monitor_tabs, daemon=True)
        self.running = True
        self.monitor_thread.start()
    
    def open_tab(self, url: str = None):
        """Abre una nueva pestaña de Chrome"""
        cmd = ["google-chrome"]
        if url:
            cmd.append(url)
        new_tab = subprocess.Popen(cmd)
        self.tabs.append(new_tab)
        return new_tab
    
    def close_all_tabs(self):
        """Cierra todas las pestañas gestionadas"""
        for tab in self.tabs:
            try:
                tab.terminate()
            except:
                pass
        self.tabs.clear()
    
    def _monitor_tabs(self):
        """Hilo que monitorea el estado de las pestañas"""
        while self.running:
            for i, tab in enumerate(self.tabs[:]):
                if tab.poll() is not None:  # Si la pestaña se cerró
                    self.tabs.pop(i)
                    print(f"Pestaña cerrada, quedan {len(self.tabs)} pestañas abiertas")
            time.sleep(1)  # Revisar cada segundo
    
    def stop(self):
        """Detiene el monitor"""
        self.running = False
        self.monitor_thread.join()