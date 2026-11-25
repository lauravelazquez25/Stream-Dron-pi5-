"""Tests de concurrencia de los hilos Camara, Procesador y SistemaStream.

No hace falta la Raspberry Pi:
- rpicam-vid y ffmpeg se reemplazan por pequeños procesos de Python, así
  se prueba de verdad el lanzamiento, la tubería, el reinicio y el apagado;
- OpenCV se reemplaza por un módulo falso que entrega frames numerados.

Toda espera tiene un tiempo límite: un test de hilos que se cuelga es peor
que uno que falla, porque no dice qué salió mal.
"""

import os
import subprocess
import sys
import threading
import time
import types

import pytest

from stream_dron import camara as modulo_camara
from stream_dron.camara import Camara
from stream_dron.config import Config
from stream_dron.estado import EstadoSistema
from stream_dron.procesador import Procesador
from stream_dron.sistema import SistemaStream

LIMITE = 5.0  # segundos máximos para cualquier espera

# Procesos que imitan al pipeline real
CAPTURA_INFINITA = [sys.executable, "-c", "import time; time.sleep(60)"]
CAPTURA_QUE_MUERE = [sys.executable, "-c", "pass"]
# Como ffmpeg: lee de stdin hasta que la captura cierra la tubería.
CODIFICADOR = [sys.executable, "-c", "import sys; sys.stdin.buffer.read()"]


def esperar(condicion, limite=LIMITE):
    fin = time.monotonic() + limite
    while time.monotonic() < fin:
        if condicion():
            return True
        time.sleep(0.02)
    return False


def detener_y_unir(hilo, evento):
    evento.set()
    hilo.join(LIMITE)
    assert not hilo.is_alive(), f"el hilo {hilo.name} no se detuvo a tiempo"


# ---------------------------------------------------------------- Cámara


@pytest.fixture
def pipeline_falso(monkeypatch):
    """Reemplaza los ejecutables reales y registra cada proceso lanzado."""
    lanzados = []
    popen_real = subprocess.Popen

    def popen_registrado(*args, **kwargs):
        proceso = popen_real(*args, **kwargs)
        lanzados.append(proceso)
        return proceso

    def configurar(captura):
        monkeypatch.setattr(modulo_camara, "buscar_ejecutable_camara", lambda: "rpicam-vid")
        monkeypatch.setattr(modulo_camara.shutil, "which", lambda nombre: "/usr/bin/" + nombre)
        monkeypatch.setattr(modulo_camara, "construir_comandos", lambda config, ejecutable: (captura, CODIFICADOR))
        monkeypatch.setattr(modulo_camara.subprocess, "Popen", popen_registrado)
        monkeypatch.setattr(Camara, "ESPERA_REINICIO", 0.05)
        return lanzados

    yield configurar
    for proceso in lanzados:  # nunca dejar procesos huérfanos, aunque el test falle
        if proceso.poll() is None:
            proceso.kill()
            proceso.wait()


def crear_camara(tmp_path):
    estado = EstadoSistema()
    detener = threading.Event()
    return Camara(Config(hls_dir=tmp_path), estado, detener), estado, detener


def test_sin_ejecutables_la_camara_informa_y_termina(tmp_path, monkeypatch):
    monkeypatch.setattr(modulo_camara, "buscar_ejecutable_camara", lambda: None)
    camara, estado, _ = crear_camara(tmp_path)
    camara.start()
    camara.join(LIMITE)
    assert not camara.is_alive()
    assert estado.instantanea()["camara"] == "no disponible"


def test_detener_termina_ambos_procesos_sin_dejar_huerfanos(tmp_path, pipeline_falso):
    lanzados = pipeline_falso(CAPTURA_INFINITA)
    camara, estado, detener = crear_camara(tmp_path)
    camara.start()
    assert esperar(lambda: estado.instantanea()["camara"] == "transmitiendo")
    assert len(lanzados) == 2 and all(p.poll() is None for p in lanzados)

    detener_y_unir(camara, detener)

    assert all(p.poll() is not None for p in lanzados), "quedó un proceso vivo"
    assert estado.instantanea()["camara"] == "detenida"
    assert estado.instantanea()["reinicios_camara"] == 0


def test_si_el_pipeline_se_cae_se_reinicia(tmp_path, pipeline_falso):
    lanzados = pipeline_falso(CAPTURA_QUE_MUERE)
    camara, estado, detener = crear_camara(tmp_path)
    camara.start()

    assert esperar(lambda: estado.instantanea()["reinicios_camara"] >= 3)
    detener_y_unir(camara, detener)

    # Cada reinicio lanza un par captura + codificador nuevo.
    assert len(lanzados) >= 6 and len(lanzados) % 2 == 0
    assert all(p.poll() is not None for p in lanzados)


def test_si_muere_el_codificador_tambien_se_termina_la_captura(tmp_path, pipeline_falso):
    lanzados = pipeline_falso(CAPTURA_INFINITA)
    camara, estado, detener = crear_camara(tmp_path)
    camara.start()
    assert esperar(lambda: len(lanzados) == 2)
    captura, codificador = lanzados

    codificador.kill()  # simula que ffmpeg se cae

    assert esperar(lambda: captura.poll() is not None), "la captura siguió viva sin codificador"
    assert esperar(lambda: estado.instantanea()["reinicios_camara"] >= 1)
    detener_y_unir(camara, detener)


def test_detener_durante_la_espera_de_reinicio_no_bloquea(tmp_path, pipeline_falso, monkeypatch):
    pipeline_falso(CAPTURA_QUE_MUERE)
    monkeypatch.setattr(Camara, "ESPERA_REINICIO", 30)  # una espera larguísima
    camara, estado, detener = crear_camara(tmp_path)
    camara.start()
    assert esperar(lambda: estado.instantanea()["camara"] == "reiniciando")

    inicio = time.monotonic()
    detener_y_unir(camara, detener)
    # Event.wait se interrumpe al instante: no hay que esperar los 30 s.
    assert time.monotonic() - inicio < 2


# ------------------------------------------------------------ Procesador


class CapturaFalsa:
    """Imita cv2.VideoCapture: entrega FRAMES frames numerados."""

    FRAMES = 6
    abiertos = []

    def __init__(self, ruta):
        self.ruta = ruta
        self.siguiente = 0
        self.liberada = False
        CapturaFalsa.abiertos.append(self)

    def isOpened(self):
        return not os.path.basename(self.ruta).startswith("roto")

    def read(self):
        if self.siguiente >= self.FRAMES:
            return False, None
        self.siguiente += 1
        return True, self.siguiente - 1

    def release(self):
        self.liberada = True


@pytest.fixture
def cv2_falso(monkeypatch):
    CapturaFalsa.abiertos = []
    monkeypatch.setitem(sys.modules, "cv2", types.SimpleNamespace(VideoCapture=CapturaFalsa))
    return CapturaFalsa


def crear_segmento(directorio, nombre, antiguedad):
    ruta = directorio / nombre
    ruta.write_bytes(b"")
    mtime = time.time() - antiguedad
    os.utime(ruta, (mtime, mtime))
    return ruta


def crear_procesador(tmp_path, analizar, **kwargs):
    estado = EstadoSistema()
    detener = threading.Event()
    return Procesador(Config(hls_dir=tmp_path), estado, detener, analizar=analizar, **kwargs), estado, detener


def test_procesa_solo_el_segmento_completo_mas_nuevo(tmp_path, cv2_falso):
    # Tres segmentos atrasados y uno que ffmpeg todavía está escribiendo.
    for i, antiguedad in enumerate([8, 6, 4, 0]):
        crear_segmento(tmp_path, f"stream{i}.ts", antiguedad)
    procesador, estado, detener = crear_procesador(tmp_path, lambda frame: {"frame": frame})
    procesador.start()

    assert esperar(lambda: estado.instantanea()["segmentos_procesados"] == 1)
    time.sleep(0.7)  # más de un ciclo de sondeo: no debe procesar nada más
    detener_y_unir(procesador, detener)

    datos = estado.instantanea()
    assert datos["segmentos_procesados"] == 1
    assert datos["ultimo_segmento"] == "stream2.ts"  # salta los atrasados y no toca stream3
    assert [os.path.basename(c.ruta) for c in cv2_falso.abiertos] == ["stream2.ts"]
    assert datos["procesador"] == "detenido"


def test_procesa_cada_segmento_nuevo_una_sola_vez(tmp_path, cv2_falso):
    crear_segmento(tmp_path, "stream0.ts", 4)
    crear_segmento(tmp_path, "stream1.ts", 2)
    procesador, estado, detener = crear_procesador(tmp_path, lambda frame: {})
    procesador.start()
    assert esperar(lambda: estado.instantanea()["ultimo_segmento"] == "stream0.ts")

    crear_segmento(tmp_path, "stream2.ts", 0)  # ahora stream1 quedó completo
    assert esperar(lambda: estado.instantanea()["ultimo_segmento"] == "stream1.ts")
    time.sleep(0.7)
    detener_y_unir(procesador, detener)

    assert estado.instantanea()["segmentos_procesados"] == 2
    assert all(c.liberada for c in cv2_falso.abiertos), "una captura quedó sin liberar"


def test_analiza_uno_de_cada_n_frames(tmp_path, cv2_falso):
    crear_segmento(tmp_path, "stream0.ts", 2)
    crear_segmento(tmp_path, "stream1.ts", 0)
    analizados = []
    procesador, estado, detener = crear_procesador(
        tmp_path, lambda frame: analizados.append(frame) or {"frame": frame}, cada_n_frames=2)
    procesador.start()
    assert esperar(lambda: estado.instantanea()["segmentos_procesados"] == 1)
    detener_y_unir(procesador, detener)

    assert analizados == [0, 2, 4]
    assert estado.instantanea()["ultimo_resultado"] == {"frame": 4}


def test_un_segmento_ilegible_no_detiene_al_procesador(tmp_path, cv2_falso):
    crear_segmento(tmp_path, "roto0.ts", 4)
    crear_segmento(tmp_path, "stream1.ts", 2)
    procesador, estado, detener = crear_procesador(tmp_path, lambda frame: {})
    procesador.start()
    time.sleep(0.3)
    assert procesador.is_alive()
    assert estado.instantanea()["segmentos_procesados"] == 0

    crear_segmento(tmp_path, "stream2.ts", 0)
    assert esperar(lambda: estado.instantanea()["ultimo_segmento"] == "stream1.ts")
    detener_y_unir(procesador, detener)


def test_detener_interrumpe_un_segmento_a_mitad_de_camino(tmp_path, cv2_falso, monkeypatch):
    monkeypatch.setattr(CapturaFalsa, "FRAMES", 10_000)
    crear_segmento(tmp_path, "stream0.ts", 2)
    crear_segmento(tmp_path, "stream1.ts", 0)
    analizando = threading.Event()

    def analisis_lento(frame):
        analizando.set()
        time.sleep(0.01)
        return {}

    procesador, estado, detener = crear_procesador(tmp_path, analisis_lento)
    procesador.start()
    assert analizando.wait(LIMITE)
    detener_y_unir(procesador, detener)  # no espera los 10 000 frames

    assert cv2_falso.abiertos[0].siguiente < 10_000
    assert cv2_falso.abiertos[0].liberada


# --------------------------------------------------------------- Sistema


def test_el_sistema_detiene_todos_sus_hilos(tmp_path, cv2_falso, monkeypatch):
    monkeypatch.setattr(modulo_camara, "buscar_ejecutable_camara", lambda: None)
    sistema = SistemaStream(Config(hls_dir=tmp_path))
    for hilo in sistema._hilos:
        hilo.start()
    assert esperar(lambda: sistema.estado.instantanea()["procesador"] == "esperando segmentos")

    sistema.detener()

    assert not any(h.is_alive() for h in sistema._hilos)
    assert sistema.estado.instantanea()["procesador"] == "detenido"
