"""Ejecuta el pipeline completo de principio a fin, en orden, y registra tiempos.

    python src/pipeline.py
"""
from __future__ import annotations

import importlib
import time
from datetime import datetime

from common import ruta, guardar_json

PASOS = [
    ("generate_data", "Generación de datos sintéticos (6 fuentes)"),
    ("ingest", "Ingesta, rezagos y resolución de identidad"),
    ("features", "Feature store precalculado"),
    ("train", "Entrenamiento v1/v2, mitigación y ablación"),
    ("explain", "Explicabilidad TreeSHAP de rechazos"),
    ("fairness", "Auditoría de equidad"),
    ("monitor", "Monitoreo de drift (PSI/KS)"),
    ("latency", "Benchmark de latencia (RNF-01)"),
    ("audit_log", "Registro de auditoría inmutable"),
    ("figuras", "Gráficos para informe y presentación"),
]


def main() -> None:
    log = []
    t_total = time.perf_counter()
    for modulo, desc in PASOS:
        print(f"\n=== {desc} ({modulo}.py) ===")
        t0 = time.perf_counter()
        importlib.import_module(modulo).main()
        log.append({"paso": modulo, "descripcion": desc, "segundos": round(time.perf_counter() - t0, 1)})
    guardar_json({"fecha": datetime.now().isoformat(timespec="seconds"), "pasos": log,
                  "segundos_total": round(time.perf_counter() - t_total, 1)},
                 ruta("reportes") / "ejecucion_pipeline.json")
    print(f"\nPipeline completo en {time.perf_counter() - t_total:.0f} s")


if __name__ == "__main__":
    main()
