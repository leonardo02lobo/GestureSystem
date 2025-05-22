import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk

class CameraApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        
        # Inicializar la cámara
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: No se pudo abrir la cámara")
            return
        
        # Crear un canvas para mostrar el video
        self.canvas = tk.Canvas(window, width=640, height=480)
        self.canvas.pack()
        
        # Botón para cerrar la aplicación
        self.btn_close = ttk.Button(window, text="Cerrar", command=self.close)
        self.btn_close.pack(pady=10)
        
        # Actualizar el video en el canvas
        self.delay = 15  # Milisegundos entre actualizaciones
        self.update()
        
        self.window.mainloop()
    
    def update(self):
        # Capturar frame de la cámara
        ret, frame = self.cap.read()
        if ret:
            # Convertir el frame de BGR (OpenCV) a RGB (Tkinter)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Redimensionar si es necesario (opcional)
            frame = cv2.resize(frame, (640, 480))
            
            # Convertir a formato compatible con Tkinter
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        
        # Llamar a la función de nuevo después de un delay
        self.window.after(self.delay, self.update)
    
    def close(self):
        # Liberar la cámara y cerrar la ventana
        if self.cap.isOpened():
            self.cap.release()
        self.window.destroy()

# Crear la ventana principal
root = tk.Tk()
app = CameraApp(root, "Cámara en Tkinter")