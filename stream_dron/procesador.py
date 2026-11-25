"""Procesamiento concurrente de los segmentos de video con OpenCV.

La función de análisis es intercambiable: hoy convierte a escala de grises
y mide el brillo; en la Etapa 2 se reemplaza por la inferencia con
TensorFlow Lite sin tocar el resto del sistema.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Callable

from . import hls
from .config import Config
from .estado import EstadoSistema

log = logging.getLogger(__name__)

# Una función de análisis recibe un frame (array BGR de numpy) y devuelve un dict.
Analisis = Callable[[Any], dict]


def analisis_escala_grises(frame) -> dict:
    import cv2

    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return {"brillo_medio": round(float(gris.mean()), 2)}


class Procesador(threading.Thread):
    """Hilo que toma el segmento completo más reciente y lo analiza.

    Prioriza la latencia: si se acumulan segmentos sin procesar, salta
    directamente al más nuevo en lugar de procesar la cola atrasada.
    """

    def __init__(
        self,
        config: Config,
        estado: EstadoSistema,
        detener: threading.Event,
        analizar: Analisis = analisis_escala_grises,
        cada_n_frames: int = 1,
    ) -> None:
        super().__init__(name="procesador", daemon=True)
        self._config = config
        self._estado = estado
        self._detener = detener
        self._analizar = analizar
        self._cada_n_frames = max(1, cada_n_frames)

    def run(self) -> None:
        self._estado.actualizar(procesador="esperando segmentos")
        vistos: set[str] = set()

        while not self._detener.is_set():
            completos = hls.segmentos_completos(self._config.hls_dir)
            nuevos = [s for s in completos if s.name not in vistos]
            if not nuevos:
                self._detener.wait(0.5)
                continue

            vistos.update(s.name for s in nuevos)
            self._procesar_segmento(nuevos[-1])
            # Olvidamos los nombres que ffmpeg ya borró para no crecer sin límite.
            vistos &= {s.name for s in completos}

        self._estado.actualizar(procesador="detenido")

    def _procesar_segmento(self, segmento: Path) -> None:
        import cv2

        captura = cv2.VideoCapture(str(segmento))
        if not captura.isOpened():
            log.warning("No se pudo abrir %s", segmento.name)
            return

        self._estado.actualizar(procesador="procesando")
        resultado = None
        indice = 0
        try:
            while not self._detener.is_set():
                ok, frame = captura.read()
                if not ok:
                    break
                if indice % self._cada_n_frames == 0:
                    resultado = self._analizar(frame)
                indice += 1
        finally:
            captura.release()

        self._estado.incrementar("segmentos_procesados")
        self._estado.actualizar(
            procesador="esperando segmentos",
            ultimo_segmento=segmento.name,
            ultimo_resultado=resultado,
        )
        log.debug("Procesado %s (%d frames): %s", segmento.name, indice, resultado)
