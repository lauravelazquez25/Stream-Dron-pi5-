"""Servidor web: página de visualización, archivos HLS y API de estado."""

from __future__ import annotations

from flask import Flask, jsonify, render_template, send_from_directory

from . import hls
from .config import Config
from .estado import EstadoSistema


def create_app(config: Config, estado: EstadoSistema | None = None) -> Flask:
    """Fábrica de la aplicación (patrón *application factory* de Flask).

    Recibir la configuración como parámetro permite crear apps aisladas
    para los tests, apuntando a directorios temporales.
    """
    app = Flask(__name__)
    estado = estado or EstadoSistema()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/hls/<path:nombre>")
    def archivos_hls(nombre: str):
        respuesta = send_from_directory(config.hls_dir, nombre)
        if nombre.endswith(".m3u8"):
            # La playlist cambia cada pocos segundos: el navegador no debe cachearla.
            respuesta.headers["Cache-Control"] = "no-cache"
        return respuesta

    @app.get("/api/estado")
    def api_estado():
        return jsonify(
            stream_activo=hls.stream_activo(config.hls_dir, config.umbral_inactividad),
            **estado.instantanea(),
        )

    return app
