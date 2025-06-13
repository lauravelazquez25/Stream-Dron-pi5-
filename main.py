from threading import Thread
import time

# -----------------------------
# FUNCIONES DE LOS SUBSISTEMAS
# -----------------------------

def iniciar_flask():
    """
    Esta función simula el servidor Flask que expone la interfaz web.
    En la práctica, ejecutaría flask_app.py.
    """
    while True:
        print("[FLASK] Servidor Flask ejecutándose...")
        time.sleep(5)  # Simula actividad del servidor

def iniciar_transmision():
    """
    Esta función simula el proceso de transmisión de video desde la cámara.
    Normalmente lanzaría iniciar_transmision.sh con ffmpeg y libcamera.
    """
    while True:
        print("[TRANSMISIÓN] Transmitiendo stream de cámara...")
        time.sleep(5)  # Simula envío de video a la carpeta HLS

def procesar_video():
    """
    Esta función representa un análisis en tiempo real de los frames de video.
    Ideal para usar OpenCV o detección con IA.
    """
    while True:
        print("[PROCESAMIENTO] Analizando frames en tiempo real...")
        time.sleep(5)  # Simula tarea de procesamiento

# -----------------------------
# LANZAMIENTO DE HILOS
# -----------------------------

if __name__ == "__main__":
    # Crear hilos para cada subsistema
    hilo_flask = Thread(target=iniciar_flask)
    hilo_transmision = Thread(target=iniciar_transmision)
    hilo_procesamiento = Thread(target=procesar_video)

    # Iniciar los hilos concurrentemente
    hilo_flask.start()
    hilo_transmision.start()
    hilo_procesamiento.start()

    # Esperar (bloquear) la ejecución principal hasta que terminen los hilos
    hilo_flask.join()
    hilo_transmision.join()
    hilo_procesamiento.join()
