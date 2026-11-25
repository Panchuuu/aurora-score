"""Monitoreo del modelo (RF-11): PSI y KS por variable y del score.

* PSI (Population Stability Index): cuánto cambió la distribución de una variable entre la
  población de entrenamiento y la que está llegando. < 0,10 estable · 0,10-0,25 vigilar ·
  > 0,25 cambio relevante.
* KS de dos muestras: distancia máxima entre las distribuciones acumuladas.

Aquí la "población que llega" es la cohorte reciente (oct-dic 2025). Como la cohorte de
entrenamiento tenía sesgo de muestra, el monitoreo debería detectarlo como drift en las
variables ligadas a ruralidad y huella digital.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import PARAMS, ruta, guardar_json, leer_json

M = PARAMS["monitoreo"]


def psi(ref: pd.Series, act: pd.Series, bins: int = 10) -> float:
    if isinstance(ref.dtype, pd.CategoricalDtype) or ref.dtype == object:
        r = ref.astype(str).value_counts(normalize=True)
        a = act.astype(str).value_counts(normalize=True)
        idx = r.index.union(a.index)
        r, a = r.reindex(idx, fill_value=0), a.reindex(idx, fill_value=0)
    else:
        ref, act = ref.astype(float), act.astype(float)
        na_r, na_a = ref.isna().mean(), act.isna().mean()
        q = np.unique(np.nanquantile(ref, np.linspace(0, 1, bins + 1)))
        if len(q) < 2:
            return 0.0
        q[0], q[-1] = -np.inf, np.inf
        r = pd.cut(ref.dropna(), q).value_counts(normalize=True, sort=False) * (1 - na_r)
        a = pd.cut(act.dropna(), q).value_counts(normalize=True, sort=False) * (1 - na_a)
        r = pd.concat([r, pd.Series([na_r])], ignore_index=True)
        a = pd.concat([a, pd.Series([na_a])], ignore_index=True)
    r, a = r.clip(lower=1e-4), a.clip(lower=1e-4)
    return float(((a - r) * np.log(a / r)).sum())


def ks_2m(ref: pd.Series, act: pd.Series) -> float:
    ref, act = np.sort(ref.dropna().astype(float)), np.sort(act.dropna().astype(float))
    if len(ref) == 0 or len(act) == 0:
        return 0.0
    v = np.concatenate([ref, act])
    return float(np.max(np.abs(np.searchsorted(ref, v, "right") / len(ref)
                               - np.searchsorted(act, v, "right") / len(act))))


def estado(p: float) -> str:
    return "crítico" if p > M["psi_critico"] else "vigilar" if p > M["psi_alerta"] else "estable"


def main() -> None:
    from train import cargar
    from decision import MotorDecision
    df = cargar()
    motor = MotorDecision()
    tr, te = df[df.cohorte == "historica"], df[df.cohorte == "reciente"]
    filas = []
    for v in motor.variables:
        es_cat = isinstance(df[v].dtype, pd.CategoricalDtype)
        p = psi(tr[v], te[v])
        filas.append({"variable": v, "psi": round(p, 4),
                      "ks": None if es_cat else round(ks_2m(tr[v], te[v]), 4), "estado": estado(p)})
    tabla = pd.DataFrame(filas).sort_values("psi", ascending=False)
    tabla.to_csv(ruta("reportes") / "monitoreo_drift.csv", index=False)

    s_tr = pd.Series(motor.probabilidad(tr))
    pred = pd.read_parquet(ruta("reportes") / "predicciones_test.parquet")
    mensual = []
    for mes, d in pred.groupby(pred.fecha_solicitud.dt.to_period("M")):
        p = psi(s_tr, d.pd_v2)
        mensual.append({"mes": str(mes), "psi_score": round(p, 4), "estado": estado(p),
                        "tasa_aprobacion": round(float(d.aprobado_v2.mean()), 4)})
    res = {"psi_score_total": round(psi(s_tr, pred.pd_v2), 4),
           "ks_score_total": round(ks_2m(s_tr, pred.pd_v2), 4),
           "variables_por_estado": tabla.estado.value_counts().to_dict(),
           "top_drift": tabla.head(8).to_dict("records"), "score_mensual": mensual}
    guardar_json(res, ruta("reportes") / "monitoreo_resumen.json")
    print(tabla.head(10).to_string(index=False))
    print(res["psi_score_total"], res["variables_por_estado"])


if __name__ == "__main__":
    main()
