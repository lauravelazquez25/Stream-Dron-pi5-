import threading

from stream_dron.camara import construir_comandos
from stream_dron.config import Config
from stream_dron.estado import EstadoSistema


def test_config_lee_entorno_y_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("STREAM_PUERTO", "8080")
    monkeypatch.setenv("STREAM_HLS_DIR", str(tmp_path))
    config = Config.desde_entorno(fps=30)
    assert config.puerto == 8080
    assert config.hls_dir == tmp_path
    assert config.fps == 30


def test_comandos_usan_la_configuracion(tmp_path):
    captura, ffmpeg = construir_comandos(Config(hls_dir=tmp_path, ancho=640, alto=480, fps=15))
    assert "640" in captura and "480" in captura and "15" in captura
    assert "640x480" in ffmpeg
    assert ffmpeg[-1] == str(tmp_path / "stream.m3u8")


def test_estado_es_seguro_entre_hilos():
    estado = EstadoSistema()

    def sumar():
        for _ in range(10_000):
            estado.incrementar("segmentos_procesados")

    hilos = [threading.Thread(target=sumar) for _ in range(8)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert estado.instantanea()["segmentos_procesados"] == 80_000
