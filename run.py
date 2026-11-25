#!/usr/bin/env python3
"""Punto de entrada: ``python run.py --help``."""

from __future__ import annotations

import argparse
import logging
import signal
import sys

from stream_dron.config import Config
from stream_dron.sistema import SistemaStream


def _parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream de video desde la Raspberry Pi 5")
    parser.add_argument("--puerto", type=int, help="puerto HTTP (por defecto 5000)")
    parser.add_argument("--sin-camara", action="store_true",
                        help="no lanzar la captura (útil para desarrollar sin la Pi)")
    parser.add_argument("--sin-procesamiento", action="store_true",
                        help="no lanzar el hilo de OpenCV")
    parser.add_argument("-v", "--verbose", action="store_true", help="logs detallados")
    return parser.parse_args(argv)


def _sigterm_como_ctrl_c(_signum, _frame) -> None:
    # systemd/docker detienen con SIGTERM: lo tratamos igual que Ctrl+C.
    raise KeyboardInterrupt


def main(argv: list[str] | None = None) -> int:
    args = _parsear_argumentos(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(threadName)s] %(levelname)s %(message)s",
    )

    signal.signal(signal.SIGTERM, _sigterm_como_ctrl_c)

    sistema = SistemaStream(
        Config.desde_entorno(puerto=args.puerto),
        con_camara=not args.sin_camara,
        con_procesador=not args.sin_procesamiento,
    )
    try:
        sistema.ejecutar()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
