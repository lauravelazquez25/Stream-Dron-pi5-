"""Utilidades para inspeccionar el directorio de salida HLS."""

from __future__ import annotations

import time
from pathlib import Path

PLAYLIST = "stream.m3u8"


def preparar_directorio(hls_dir: Path) -> None:
    """Crea el directorio y borra restos de una transmisión anterior."""
    hls_dir.mkdir(parents=True, exist_ok=True)
    for archivo in hls_dir.iterdir():
        if archivo.suffix in (".ts", ".m3u8", ".tmp"):
            archivo.unlink(missing_ok=True)


def segmentos(hls_dir: Path) -> list[Path]:
    """Segmentos .ts ordenados del más viejo al más nuevo.

    Se ordena por fecha de modificación y NO por nombre: ``stream10.ts``
    va antes que ``stream2.ts`` en orden alfabético.
    """
    if not hls_dir.is_dir():
        return []
    ts = [p for p in hls_dir.iterdir() if p.suffix == ".ts"]
    return sorted(ts, key=lambda p: p.stat().st_mtime)


def segmentos_completos(hls_dir: Path) -> list[Path]:
    """Todos los segmentos menos el último, que ffmpeg puede estar escribiendo."""
    return segmentos(hls_dir)[:-1]


def stream_activo(hls_dir: Path, umbral: float, ahora: float | None = None) -> bool:
    """Hay stream si existe un segmento más reciente que ``umbral`` segundos."""
    lista = segmentos(hls_dir)
    if not lista:
        return False
    ahora = time.time() if ahora is None else ahora
    return ahora - lista[-1].stat().st_mtime < umbral
