# camera_capture.py
import cv2
import os
import datetime

def capture_photo(save_dir="photos"):
    """
    Abre la cámara del dispositivo y permite tomar una foto.
    - Presiona ESPACIO para capturar.
    - Presiona ESC para salir.
    La foto se guarda en save_dir.
    """
    # Crear carpeta si no existe
    os.makedirs(save_dir, exist_ok=True)

    # Abrir la cámara (índice 0 = cámara principal)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ No se pudo acceder a la cámara.")
        return None

    print("📸 Cámara iniciada. Presiona [ESPACIO] para tomar foto, [ESC] para salir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error al leer la imagen de la cámara.")
            break

        # Mostrar video en vivo
        cv2.imshow("Captura de Foto", frame)

        # Esperar tecla
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC para salir
            print("🚪 Saliendo sin capturar.")
            break
        elif key == 32:  # ESPACIO para capturar
            filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
            filepath = os.path.join(save_dir, filename)
            cv2.imwrite(filepath, frame)
            print(f"✅ Foto guardada en {filepath}")
            break

    cap.release()
    cv2.destroyAllWindows()
    return filepath if 'filepath' in locals() else None

if __name__ == "__main__":
    capture_photo()
