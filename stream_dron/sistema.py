"""Orquestador: el "objeto concurrente accesible por IP".

Agrupa los tres subsistemas (cámara, procesador, servidor web), los inicia
en hilos separados y coordina su apagado mediante un único ``Event``.
"""

from __future__ import annotations

import logging
import threading

from .camara import Camara
from .config import Config
from .estado import EstadoSistema
from .procesador import Procesador
from .web import create_app

log = logging.getLogger(__name__)


class SistemaStream:
    def __init__(self, config: Config, con_camara: bool = True, con_procesador: bool = True) -> None:
        self.config = config
        self.estado = EstadoSistema()
        self._detener = threading.Event()
        self._hilos: list[threading.Thread] = []
        if con_camara:
            self._hilos.append(Camara(config, self.estado, self._detener))
        if con_procesador:
            self._hilos.append(Procesador(config, self.estado, self._detener))
        self.app = create_app(config, self.estado)

    def ejecutar(self) -> None:
        """Inicia los hilos y bloquea sirviendo HTTP hasta Ctrl+C / SIGTERM."""
        self.config.hls_dir.mkdir(parents=True, exist_ok=True)
        for hilo in self._hilos:
            hilo.start()
        log.info("Servidor en http://%s:%d", self.config.host, self.config.puerto)
        try:
            # Flask ocupa el hilo principal; cada petición se atiende en su propio hilo.
            self.app.run(host=self.config.host, port=self.config.puerto, threaded=True, use_reloader=False)
        finally:
            self.detener()

    def detener(self) -> None:
        log.info("Deteniendo subsistemas...")
        self._detener.set()
        for hilo in self._hilos:
            hilo.join(timeout=10)
