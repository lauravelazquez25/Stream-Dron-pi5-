"""Captura de la cámara CSI y codificación a HLS.

Reemplaza a ``iniciar_transmision.sh``: el pipeline es el mismo
(``rpicam-vid | ffmpeg``), pero ahora lo controla un hilo de Python que
puede detenerlo limpiamente y reiniciarlo si se cae.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import threading

from . import hls
from .config import Config
from .estado import EstadoSistema

log = logging.getLogger(__name__)

# En Raspberry Pi OS Bookworm ``libcamera-vid`` pasó a llamarse ``rpicam-vid``.
_CANDIDATOS_CAMARA = ("rpicam-vid", "libcamera-vid")


def buscar_ejecutable_camara() -> str | None:
    return next((c for c in _CANDIDATOS_CAMARA if shutil.which(c)), None)


def construir_comandos(config: Config, ejecutable: str = "rpicam-vid") -> tuple[list[str], list[str]]:
    """Devuelve (comando_captura, comando_ffmpeg) como listas de argumentos."""
    resolucion = f"{config.ancho}x{config.alto}"
    captura = [
        ejecutable,
        "--width", str(config.ancho),
        "--height", str(config.alto),
        "--framerate", str(config.fps),
        "--codec", "yuv420",
        "--nopreview",
        "-t", "0",
        "-o", "-",
    ]
    # La Pi 5 no tiene codificador H.264 por hardware: libx264 por software.
    ffmpeg = [
        "ffmpeg", "-loglevel", "warning",
        "-f", "rawvideo", "-pixel_format", "yuv420p",
        "-video_size", resolucion, "-framerate", str(config.fps),
        "-i", "-",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
        "-g", str(config.fps * config.duracion_segmento),  # un keyframe por segmento
        "-f", "hls",
        "-hls_time", str(config.duracion_segmento),
        "-hls_list_size", str(config.segmentos_en_lista),
        "-hls_flags", "delete_segments",
        str(config.hls_dir / hls.PLAYLIST),
    ]
    return captura, ffmpeg


class Camara(threading.Thread):
    """Hilo supervisor del pipeline de captura.

    Lanza los procesos, vigila que sigan vivos y los reinicia si alguno
    termina inesperadamente. Se detiene cuando se activa el ``Event``.
    """

    ESPERA_REINICIO = 3.0  # segundos

    def __init__(self, config: Config, estado: EstadoSistema, detener: threading.Event) -> None:
        super().__init__(name="camara", daemon=True)
        self._config = config
        self._estado = estado
        self._detener = detener
        self._procesos: list[subprocess.Popen] = []

    def run(self) -> None:
        ejecutable = buscar_ejecutable_camara()
        if ejecutable is None or shutil.which("ffmpeg") is None:
            log.error("No se encontró rpicam-vid/libcamera-vid o ffmpeg; la cámara no se inicia.")
            self._estado.actualizar(camara="no disponible")
            return

        hls.preparar_directorio(self._config.hls_dir)
        cmd_captura, cmd_ffmpeg = construir_comandos(self._config, ejecutable)

        while not self._detener.is_set():
            self._lanzar(cmd_captura, cmd_ffmpeg)
            self._estado.actualizar(camara="transmitiendo")
            log.info("Transmisión iniciada (%s | ffmpeg)", ejecutable)

            # Espera hasta que pidan detener o algún proceso muera.
            while not self._detener.is_set() and all(p.poll() is None for p in self._procesos):
                self._detener.wait(0.5)

            self._terminar()
            if not self._detener.is_set():
                log.warning("El pipeline de captura terminó; reiniciando en %.0f s", self.ESPERA_REINICIO)
                self._estado.actualizar(camara="reiniciando")
                self._estado.incrementar("reinicios_camara")
                self._detener.wait(self.ESPERA_REINICIO)

        self._estado.actualizar(camara="detenida")

    def _lanzar(self, cmd_captura: list[str], cmd_ffmpeg: list[str]) -> None:
        captura = subprocess.Popen(cmd_captura, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        codificador = subprocess.Popen(cmd_ffmpeg, stdin=captura.stdout)
        # Cerramos nuestra copia del pipe: si ffmpeg muere, la captura recibe SIGPIPE.
        captura.stdout.close()
        self._procesos = [captura, codificador]

    def _terminar(self) -> None:
        for proceso in self._procesos:
            if proceso.poll() is None:
                proceso.terminate()
        for proceso in self._procesos:
            try:
                proceso.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proceso.kill()
        self._procesos = []
