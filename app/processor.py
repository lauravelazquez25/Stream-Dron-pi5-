# app/processor.py
import cv2  # Librería principal de procesamiento de imágenes
import os
import time

# Ruta a la carpeta donde se generan los fragmentos de video HLS
HLS_DIR = "../static/hls"

def procesar_stream():
    """
    Esta función busca el último fragmento de video (.ts) generado por ffmpeg
    y lo procesa frame por frame en escala de grises usando OpenCV.
    """

    print("[INFO] Iniciando procesamiento con OpenCV...")

    while True:
        # Lista de todos los archivos .ts generados por el stream
        ts_files = sorted([f for f in os.listdir(HLS_DIR) if f.endswith(".ts")])

        if not ts_files:
            print("[INFO] No se encontraron archivos .ts aún...")
            time.sleep(1)
            continue  # Espera hasta que se genere al menos un fragmento

        # Selecciona el último archivo .ts para procesar (el más reciente)
        ultimo_ts = os.path.join(HLS_DIR, ts_files[-1])
        print(f"[INFO] Procesando archivo: {ultimo_ts}")

        # Intenta abrir el archivo con OpenCV
        cap = cv2.VideoCapture(ultimo_ts)

        if not cap.isOpened():
            print("[ERROR] No se pudo abrir el archivo de video.")
            time.sleep(1)
            continue

        while True:
            ret, frame = cap.read()  # Lee el siguiente frame

            if not ret:
                break  # Fin del archivo .ts

            # Aplica un filtro (en este caso, convierte a escala de grises)
            gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Muestra el resultado en una ventana
            cv2.imshow("Procesamiento OpenCV", gris)

            # Espera 1 ms. Si se presiona la tecla 'q', sale del loop interno
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[INFO] Se interrumpió manualmente el procesamiento.")
                cap.release()
                cv2.destroyAllWindows()
                return

        cap.release()  # Libera el archivo .ts después de leerlo
        time.sleep(1)  # Espera un segundo antes de analizar el siguiente archivo

