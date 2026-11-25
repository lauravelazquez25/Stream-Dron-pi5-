import os
import time

from stream_dron import hls


def _crear_segmento(directorio, nombre, mtime):
    ruta = directorio / nombre
    ruta.write_bytes(b"")
    os.utime(ruta, (mtime, mtime))
    return ruta


def test_segmentos_se_ordenan_por_fecha_y_no_por_nombre(tmp_path):
    ahora = time.time()
    _crear_segmento(tmp_path, "stream2.ts", ahora - 20)
    _crear_segmento(tmp_path, "stream10.ts", ahora - 10)
    assert [p.name for p in hls.segmentos(tmp_path)] == ["stream2.ts", "stream10.ts"]


def test_segmentos_completos_excluye_el_que_se_esta_escribiendo(tmp_path):
    ahora = time.time()
    _crear_segmento(tmp_path, "stream0.ts", ahora - 4)
    _crear_segmento(tmp_path, "stream1.ts", ahora)
    assert [p.name for p in hls.segmentos_completos(tmp_path)] == ["stream0.ts"]


def test_stream_activo_segun_umbral(tmp_path):
    ahora = time.time()
    assert not hls.stream_activo(tmp_path, umbral=10, ahora=ahora)
    _crear_segmento(tmp_path, "stream0.ts", ahora - 30)
    assert not hls.stream_activo(tmp_path, umbral=10, ahora=ahora)
    _crear_segmento(tmp_path, "stream1.ts", ahora - 2)
    assert hls.stream_activo(tmp_path, umbral=10, ahora=ahora)


def test_directorio_inexistente(tmp_path):
    assert hls.segmentos(tmp_path / "no_existe") == []


def test_preparar_directorio_limpia_restos(tmp_path):
    destino = tmp_path / "hls"
    destino.mkdir()
    (destino / "viejo.ts").write_bytes(b"")
    (destino / "stream.m3u8").write_text("")
    hls.preparar_directorio(destino)
    assert list(destino.iterdir()) == []
