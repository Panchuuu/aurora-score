"""Benchmark de latencia de la ruta crítica de decisión (RNF-01: < 8 s en percentil 95).

Se ejecuta la ruta completa para N solicitudes, una a una, como llegarían en producción:

  1 recepción · 2 resolución de identidad · 3 lectura del feature store · 4 variables al
  vuelo · 5 llamadas a terceros (timeout duro) · 6 inferencia · 7 reglas · 8 SHAP · 9 respuesta

Componentes MEDIDOS (se ejecutan de verdad y se cronometran en esta máquina): 2, 4, 6, 7, 8 y
el cómputo de 1, 3 y 9.
Componentes SIMULADOS (no hay red real en el prototipo): la latencia de red de 1 y 9, la E/S
del feature store en 3 y la respuesta de terceros en 5. Se muestrean de distribuciones
log-normales con colas pesadas, deliberadamente pesimistas respecto del presupuesto del plan.

El registro de auditoría, la carta de explicación y las notificaciones quedan FUERA de la ruta
crítica (escritura asíncrona), como define la arquitectura.
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from common import PARAMS, ruta, rng, guardar_json
from decision import MotorDecision
import identity

L = PARAMS["latencia"]
# mediana (ms), sigma log-normal — red y E/S simuladas
SIMULADO = {"red_entrada": (120, 0.5), "io_feature_store": (60, 0.6), "terceros": (650, 0.55),
            "red_salida": (120, 0.5)}


def _lognormal(g, mediana, sigma):
    return float(mediana * np.exp(g.normal(0, sigma)))


def main() -> None:
    g = rng(77)
    motor = MotorDecision()
    fs = pd.read_parquet(ruta("features") / "feature_store.parquet")
    sol_raw = pd.read_parquet(ruta("raw") / "solicitudes.parquet")
    # índice de identidad precargado en memoria (como un servicio de resolución)
    indice_id = {identity.normalizar_telefono(t): i for t, i in zip(sol_raw.telefono, sol_raw.solicitud_id)}
    fs = fs.set_index("solicitud_id")
    store = {i: fs.loc[[i]] for i in fs[fs.cohorte == "reciente"].index[: L["n_solicitudes"]]}
    ids = list(store)
    tels = sol_raw.set_index("solicitud_id").telefono

    filas = []
    for sid in ids:
        t = {}
        payload = json.dumps({"solicitud_id": int(sid), "telefono": tels[sid], "monto": 320})

        t0 = time.perf_counter(); req = json.loads(payload)
        t["1_recepcion"] = (time.perf_counter() - t0) * 1000 + _lognormal(g, *SIMULADO["red_entrada"])

        t0 = time.perf_counter(); pid = indice_id[identity.normalizar_telefono(req["telefono"])]
        t["2_identidad"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter(); X = store[pid].copy()
        t["3_feature_store"] = (time.perf_counter() - t0) * 1000 + _lognormal(g, *SIMULADO["io_feature_store"])

        t0 = time.perf_counter()
        X["cuota_sobre_recarga"] = (req["monto"] * (1 + 0.031 * X.plazo_meses) / X.plazo_meses
                                    / X.monto_recargas_medio.clip(lower=1))
        t["4_variables_al_vuelo"] = (time.perf_counter() - t0) * 1000

        lat_terc = _lognormal(g, *SIMULADO["terceros"])
        timeout = lat_terc > L["timeout_terceros_ms"]
        t["5_terceros"] = min(lat_terc, L["timeout_terceros_ms"])

        t0 = time.perf_counter(); p = float(motor.booster.predict(X[motor.variables])[0])
        t["6_inferencia"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter(); aprobado = p <= motor.umbrales[X.pais.iloc[0]]
        t["7_reglas"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter(); motor.booster.predict(X[motor.variables], pred_contrib=True)
        t["8_shap"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter(); json.dumps({"solicitud_id": int(sid), "pd": p, "aprobado": bool(aprobado)})
        t["9_respuesta"] = (time.perf_counter() - t0) * 1000 + _lognormal(g, *SIMULADO["red_salida"])

        t["total"] = sum(t.values())
        t["timeout_terceros"] = timeout
        filas.append(t)

    df = pd.DataFrame(filas)
    df.to_csv(ruta("reportes") / "latencia_mediciones.csv", index=False)
    comp = [c for c in df.columns if c[0].isdigit()]
    res = {
        "n_solicitudes": len(df),
        "p50_ms": round(df.total.quantile(0.50), 1), "p95_ms": round(df.total.quantile(0.95), 1),
        "p99_ms": round(df.total.quantile(0.99), 1), "max_ms": round(df.total.max(), 1),
        "limite_p95_ms": L["p95_max_ms"], "cumple_rnf01": bool(df.total.quantile(0.95) < L["p95_max_ms"]),
        "holgura_p95_ms": round(L["p95_max_ms"] - df.total.quantile(0.95), 1),
        "pct_timeout_terceros": round(float(df.timeout_terceros.mean()) * 100, 2),
        "p95_por_componente_ms": {c: round(df[c].quantile(0.95), 2) for c in comp},
        "medio_por_componente_ms": {c: round(df[c].mean(), 2) for c in comp},
        "componentes_simulados": list(SIMULADO),
    }
    guardar_json(res, ruta("reportes") / "latencia_resumen.json")
    print({k: v for k, v in res.items() if not isinstance(v, dict)})
    print(res["p95_por_componente_ms"])


if __name__ == "__main__":
    main()
