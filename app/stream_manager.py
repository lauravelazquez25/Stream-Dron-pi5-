# app/stream_manager.py

import os
import time

# Ruta donde se generan los archivos HLS (video segmentado)
HLS_DIR = os.path.join(os.path.dirname(__file__), '../static/hls')

# Tiempo máximo permitido sin detectar archivos nuevos (en segundos)
INACTIVITY_THRESHOLD = 10

def is_stream_active():
    """
    Verifica si hay archivos recientes en el directorio HLS,
    lo que indica que el stream está activo.
    """
    if not os.path.exists(HLS_DIR):
        return False  # Si no existe el directorio, no hay stream

    now = time.time()  # Tiempo actual en segundos desde epoch
    for filename in os.listdir(HLS_DIR):
        if filename.endswith('.ts'):
            filepath = os.path.join(HLS_DIR, filename)
            last_modified = os.path.getmtime(filepath)
            if now - last_modified < INACTIVITY_THRESHOLD:
                return True  # Hay actividad reciente

    return False  # No se detectaron archivos recientes
