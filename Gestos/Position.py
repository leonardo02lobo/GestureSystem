import cv2
import mediapipe as mp
import numpy as np
import time
import platform
import subprocess # Para ejecutar comandos en Linux
# Asegúrate de tener pynput instalado para simular teclas
import pynput.keyboard

# Si usas pyautogui, también asegúrate de tenerlo instalado
try:
    import pyautogui
except ImportError:
    print("pyautogui no está instalado. El control de Windows podría no funcionar.")
    pyautogui = None

# Si usas pyvda en Windows (opcional), instala: pip install pyvda
# try:
#     from pyvda import VirtualDesktop
# except ImportError:
#     print("pyvda no está instalado. El control de escritorios de Windows podría ser limitado.")
#     VirtualDesktop = None


# Definir umbrales (ajusta estos valores experimentalmente)
UMBRAL_DISTANCIA_SWIPE_X = 0.15 # Distancia horizontal de movimiento para activar el swipe (normalizada)
UMBRAL_DISTANCIA_SWIPE_Y = 0.05 # Distancia vertical máxima permitida durante el swipe
MAX_HISTORIAL_POSICIONES = 10 # Número de frames para evaluar el movimiento
TIEMPO_ENTRE_CAMBIOS = 1.0 # Segundos mínimos entre cambios de escritorio para evitar spam

# Asumo que GestosController está en un archivo llamado GestosController.py
from GestosController import GestosController

class PositionController(GestosController):
    def __init__(self, nombre, encendido):
        super().__init__(nombre, encendido)
        # No necesitamos posicionInicial, posicionFinal, posicionActual directamente para este gesto.
        # En su lugar, usaremos un historial de posiciones.
        self.historial_posiciones = []
        self.ultimo_cambio_escritorio = 0 # Para el cooldown

    def _cambiar_escritorio(self, direccion):
        if time.time() - self.ultimo_cambio_escritorio < TIEMPO_ENTRE_CAMBIOS:
            print(f"[{self.nombre}] Esperando antes del siguiente cambio de escritorio...")
            return

        print(f"[{self.nombre}] Cambiando escritorio: {direccion}")
        if platform.system() == "Windows":
            if pyautogui:
                if direccion == "derecha":
                    pyautogui.hotkey('win', 'ctrl', 'right')
                elif direccion == "izquierda":
                    pyautogui.hotkey('win', 'ctrl', 'left')
            else:
                print("pyautogui no está disponible para cambiar escritorio en Windows.")

            # Con pyvda (si se instala y se prefiere para más control)
            # if VirtualDesktop:
            #     current_desktop_num = VirtualDesktop.current().number
            #     if direccion == "derecha":
            #         if current_desktop_num < len(VirtualDesktop.get_virtual_desktops()):
            #             VirtualDesktop(current_desktop_num + 1).go()
            #     elif direccion == "izquierda":
            #         if current_desktop_num > 1:
            #             VirtualDesktop(current_desktop_num - 1).go()
            # else:
            #     print("pyvda no está disponible para un control directo de escritorios en Windows.")

        elif platform.system() == "Linux":
            # Simular Ctrl + Alt + Flecha Derecha/Izquierda (común en GNOME, KDE, XFCE con Xorg)
            keyboard = pynput.keyboard.Controller()
            if direccion == "derecha":
                with keyboard.pressed(pynput.keyboard.Key.alt):
                    with keyboard.pressed(pynput.keyboard.Key.ctrl):
                        keyboard.press(pynput.keyboard.Key.right)
                        keyboard.release(pynput.keyboard.Key.right)
            elif direccion == "izquierda":
                with keyboard.pressed(pynput.keyboard.Key.alt):
                    with keyboard.pressed(pynput.keyboard.Key.ctrl):
                        keyboard.press(pynput.keyboard.Key.left)
                        keyboard.release(pynput.keyboard.Key.left)
            # Puedes descomentar las opciones de xdotool/wmctrl si prefieres
            # y asegúrate de que estén instaladas en tu sistema:
            # subprocess.run(["xdotool", "key", "super+Page_Down"])
            # subprocess.run(["wmctrl", "-s", "next_desktop_index"])
        else:
            print(f"[{self.nombre}] Sistema operativo no soportado para cambiar escritorios.")

        self.ultimo_cambio_escritorio = time.time()

    def detectarGestos(self, hand_landmarks):
        if not hand_landmarks:
            self.historial_posiciones.clear()
            return None

        # Usar la muñeca como punto de anclaje para el deslizamiento
        # mp.solutions.hands.HandLandmark.WRIST es el punto 0
        wrist = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.WRIST]
        
        current_x = wrist.x
        current_y = wrist.y

        self.historial_posiciones.append((current_x, current_y, time.time()))

        # Mantener el historial limpio
        if len(self.historial_posiciones) > MAX_HISTORIAL_POSICIONES:
            self.historial_posiciones.pop(0)

        # Necesitamos al menos dos puntos para calcular movimiento
        if len(self.historial_posiciones) > 2:
            start_x, start_y, _ = self.historial_posiciones[0]
            
            delta_x = current_x - start_x
            delta_y = current_y - start_y

            # Deslizamiento a la DERECHA
            if delta_x > UMBRAL_DISTANCIA_SWIPE_X and abs(delta_y) < UMBRAL_DISTANCIA_SWIPE_Y:
                self.historial_posiciones.clear() # Limpiar para evitar múltiples activaciones
                self._cambiar_escritorio("derecha")
                return "deslizamiento_derecha"
            
            # Deslizamiento a la IZQUIERDA
            elif delta_x < -UMBRAL_DISTANCIA_SWIPE_X and abs(delta_y) < UMBRAL_DISTANCIA_SWIPE_Y:
                self.historial_posiciones.clear() # Limpiar para evitar múltiples activaciones
                self._cambiar_escritorio("izquierda")
                return "deslizamiento_izquierda"

        return None