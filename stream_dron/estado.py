"""Estado compartido entre hilos.

Varios hilos (cámara, procesador, servidor web) leen y escriben este objeto
al mismo tiempo. El ``Lock`` garantiza que cada lectura/escritura sea atómica
y que el servidor web nunca vea un estado a medio actualizar.
"""

from __future__ import annotations

import threading
from typing import Any


class EstadoSistema:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._datos: dict[str, Any] = {
            "camara": "detenida",
            "reinicios_camara": 0,
            "procesador": "detenido",
            "segmentos_procesados": 0,
            "ultimo_segmento": None,
            "ultimo_resultado": None,
        }

    def actualizar(self, **cambios: Any) -> None:
        with self._lock:
            self._datos.update(cambios)

    def incrementar(self, clave: str, cantidad: int = 1) -> None:
        with self._lock:
            self._datos[clave] = self._datos.get(clave, 0) + cantidad

    def instantanea(self) -> dict[str, Any]:
        """Devuelve una copia: quien la recibe puede usarla sin tomar el lock."""
        with self._lock:
            return dict(self._datos)
