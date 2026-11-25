# Stream-Dron Pi5

Proyecto final de *Introducción a los Sistemas Distribuidos y Paralelos* (UNRN). Transmite en HLS el video de la cámara CSI de una Raspberry Pi 5, con hilos separados para la captura, el procesamiento con OpenCV y el servidor Flask. La arquitectura está en el README.

## Comandos

```bash
pip install -r requirements-dev.txt
python -m pytest
python run.py --sin-camara    # servidor sin la cámara, para desarrollar en una PC
```

## Entorno

- **No hay cámara ni Raspberry Pi en el entorno de desarrollo.** `rpicam-vid` y `ffmpeg` no están instalados: no intentar ejecutarlos. Indicar siempre qué falta probar en la Pi.
- Python 3.11 (Raspberry Pi OS Bookworm). En la Pi, OpenCV puede venir de `apt` (`python3-opencv`).
- `cv2` se importa dentro de las funciones, no al inicio del módulo: así los tests corren sin OpenCV.

## Concurrencia (lo central de la materia)

- El estado compartido entre hilos pasa **solo** por `EstadoSistema`, que usa un `Lock`. No agregar atributos compartidos fuera de él.
- El apagado se coordina con un único `threading.Event`. Para esperar, usar `self._detener.wait(t)` y nunca `time.sleep(t)`: si no, el hilo no responde al apagado.
- Todo cambio en `Camara`, `Procesador` o `SistemaStream` debe mantener en verde `tests/test_hilos.py`.

## Tests

- `tests/test_hilos.py` reemplaza `rpicam-vid`/`ffmpeg` por procesos de Python reales y `cv2` por un módulo falso.
- Toda espera en un test debe tener un tiempo límite: un test de hilos colgado no informa qué falló.
- Un test nuevo de concurrencia tiene que poder fallar: verificarlo introduciendo el error que pretende detectar.
