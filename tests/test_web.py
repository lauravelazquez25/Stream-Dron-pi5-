import time

from stream_dron.config import Config
from stream_dron.estado import EstadoSistema
from stream_dron.web import create_app


def _cliente(tmp_path, estado=None):
    app = create_app(Config(hls_dir=tmp_path), estado)
    app.testing = True
    return app.test_client()


def test_index(tmp_path):
    respuesta = _cliente(tmp_path).get("/")
    assert respuesta.status_code == 200
    assert b"Esperando" in respuesta.data


def test_api_estado_sin_stream(tmp_path):
    datos = _cliente(tmp_path).get("/api/estado").get_json()
    assert datos["stream_activo"] is False
    assert datos["camara"] == "detenida"


def test_api_estado_refleja_estado_compartido(tmp_path):
    estado = EstadoSistema()
    estado.actualizar(camara="transmitiendo")
    (tmp_path / "stream0.ts").write_bytes(b"")
    datos = _cliente(tmp_path, estado).get("/api/estado").get_json()
    assert datos["stream_activo"] is True
    assert datos["camara"] == "transmitiendo"


def test_playlist_sin_cache(tmp_path):
    (tmp_path / "stream.m3u8").write_text("#EXTM3U\n")
    respuesta = _cliente(tmp_path).get("/hls/stream.m3u8")
    assert respuesta.status_code == 200
    assert respuesta.headers["Cache-Control"] == "no-cache"


def test_no_permite_salir_del_directorio_hls(tmp_path):
    hls_dir = tmp_path / "hls"
    hls_dir.mkdir()
    (tmp_path / "secreto.txt").write_text("x")
    respuesta = _cliente(hls_dir).get("/hls/../secreto.txt")
    assert respuesta.status_code == 404
