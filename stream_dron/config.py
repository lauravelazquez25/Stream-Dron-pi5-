"""Configuración centralizada del sistema.

Todos los parámetros viven en un único lugar. Cada uno puede sobreescribirse
con una variable de entorno (prefijo ``STREAM_``), así el mismo código corre
en la Raspberry Pi y en una notebook de desarrollo sin editar archivos.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, fields
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    # Directorio donde ffmpeg escribe la lista .m3u8 y los segmentos .ts
    hls_dir: Path = RAIZ_PROYECTO / "hls_output"

    # Parámetros de captura
    ancho: int = 1280
    alto: int = 720
    fps: int = 25

    # Parámetros HLS
    duracion_segmento: int = 2      # segundos por segmento .ts
    segmentos_en_lista: int = 10    # segmentos que conserva la playlist

    # Servidor web
    host: str = "0.0.0.0"
    puerto: int = 5000

    # Si no aparece un segmento nuevo en este tiempo, el stream se considera caído
    umbral_inactividad: float = 10.0

    @classmethod
    def desde_entorno(cls, **overrides) -> "Config":
        """Crea la configuración leyendo ``STREAM_<CAMPO>`` del entorno.

        Los ``overrides`` (por ejemplo, argumentos de línea de comandos)
        tienen prioridad sobre el entorno.
        """
        valores = {}
        for campo in fields(cls):
            crudo = os.environ.get(f"STREAM_{campo.name.upper()}")
            if crudo is not None:
                # Convertimos el texto al tipo del valor por defecto (int, float, Path...)
                valores[campo.name] = type(campo.default)(crudo)
        valores.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**valores)
