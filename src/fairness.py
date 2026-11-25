"""Auditoría de equidad (RF-11) y detección de variables proxy.

Criterios del plan (EP3):
* Brecha máxima de 5 puntos porcentuales en la tasa de aprobación entre grupos.
* Disparate impact ratio (aprobación del grupo menos favorecido / más favorecido) >= 0,80.

Los atributos protegidos viven en una tabla separada y solo se usan aquí; nunca son
variables del modelo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import PARAMS

EQ = PARAMS["equidad"]
ATRIBUTOS = EQ["atributos_protegidos"]


# ------------------------------------------------------------------ proxies
def _eta(x: pd.Series, grupo: pd.Series) -> float:
    """Razón de correlación (numérica vs categórica), 0 a 1."""
    m = x.notna()
    x, grupo = x[m].astype(float), grupo[m]
    if x.var() == 0 or len(x) < 10:
        return 0.0
    medias = x.groupby(grupo).transform("mean")
    return float(np.sqrt(((medias - x.mean()) ** 2).sum() / ((x - x.mean()) ** 2).sum()))


def _cramer_v(a: pd.Series, b: pd.Series) -> float:
    t = pd.crosstab(a, b).to_numpy().astype(float)
    if t.shape[0] < 2 or t.shape[1] < 2:
        return 0.0
    n = t.sum()
    esp = t.sum(1, keepdims=True) @ t.sum(0, keepdims=True) / n
    chi2 = ((t - esp) ** 2 / esp).sum()
    k = min(t.shape) - 1
    return float(np.sqrt(chi2 / (n * k)))


def correlacion_proxies(X: pd.DataFrame, prot: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for col in X.columns:
        fila = {"variable": col}
        for a in ATRIBUTOS:
            if isinstance(X[col].dtype, pd.CategoricalDtype):
                fila[a] = _cramer_v(X[col].astype(str), prot[a])
            else:
                fila[a] = _eta(X[col], prot[a])
        filas.append(fila)
    df = pd.DataFrame(filas).set_index("variable").round(3)
    df["max"] = df[ATRIBUTOS].max(axis=1)
    df["atributo_max"] = df[ATRIBUTOS].idxmax(axis=1)
    df["es_proxy"] = df["max"] > EQ["umbral_correlacion_proxy"]
    return df.sort_values("max", ascending=False)


# ------------------------------------------------------------------ métricas por grupo
def metricas_por_grupo(df: pd.DataFrame) -> pd.DataFrame:
    """df debe traer: aprobado (0/1), incumplio (0/1 real) y los atributos protegidos."""
    filas = []
    for a in ATRIBUTOS:
        for grupo, d in df.groupby(a):
            buenos = d[d.incumplio == 0]
            filas.append({
                "atributo": a, "grupo": grupo, "n": len(d),
                "tasa_aprobacion": d.aprobado.mean(),
                "tpr_buenos_pagadores": buenos.aprobado.mean() if len(buenos) else np.nan,
                "incumplimiento_real": d.incumplio.mean(),
                "mora_aprobados": d[d.aprobado == 1].incumplio.mean(),
            })
    return pd.DataFrame(filas)


def resumen_brechas(m: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for a, d in m.groupby("atributo", sort=False):
        ap = d.tasa_aprobacion
        filas.append({
            "atributo": a,
            "grupo_min": d.loc[ap.idxmin(), "grupo"], "aprob_min": ap.min(),
            "grupo_max": d.loc[ap.idxmax(), "grupo"], "aprob_max": ap.max(),
            "brecha_aprobacion_pp": (ap.max() - ap.min()) * 100,
            "brecha_tpr_pp": (d.tpr_buenos_pagadores.max() - d.tpr_buenos_pagadores.min()) * 100,
            "disparate_impact": ap.min() / ap.max(),
        })
    r = pd.DataFrame(filas)
    r["cumple_5pp"] = r.brecha_aprobacion_pp <= EQ["brecha_max_pp"]
    r["cumple_80"] = r.disparate_impact >= EQ["regla_80"]
    return r


def inclusion_efectiva(d: pd.DataFrame) -> dict:
    """KPI de inclusión: % de los aprobados que pertenece a grupos subrepresentados."""
    sub = ((d.zona == "rural") | (d.tramo_edad == "60+")
           | ((d.genero == "F") & (d.sector_laboral == "informal")))
    ap = d.aprobado == 1
    return {"pct_aprobados_subrepresentados": round(float(sub[ap].mean()) * 100, 2),
            "pct_solicitantes_subrepresentados": round(float(sub.mean()) * 100, 2),
            "tasa_aprobacion_subrepresentados": round(float(d.aprobado[sub].mean()) * 100, 2),
            "tasa_aprobacion_resto": round(float(d.aprobado[~sub].mean()) * 100, 2)}


def main() -> None:
    from common import ruta, guardar_json
    pred = pd.read_parquet(ruta("reportes") / "predicciones_test.parquet")
    bio = pd.read_parquet(ruta("raw") / "biometria.parquet")
    salida, tablas = {}, []
    for etiqueta, col in (("v1-base", "aprobado_v1"), ("v1-base (mismo volumen que v2)", "aprobado_v1_mismo_volumen"),
                          ("v2-mitigado", "aprobado_v2")):
        d = pred.rename(columns={col: "aprobado"})
        m = metricas_por_grupo(d)
        r = resumen_brechas(m)
        tablas.append(m.assign(modelo=etiqueta))
        r.assign(modelo=etiqueta).to_csv(ruta("reportes") / f"equidad_brechas_{col}.csv", index=False)
        salida[etiqueta] = {"veredicto": veredicto(r), "inclusion": inclusion_efectiva(d),
                            "brechas": r.round(4).to_dict("records")}
    pd.concat(tablas).to_csv(ruta("reportes") / "equidad_por_grupo.csv", index=False)

    # Foco 7 del EP1: falla biométrica diferencial (no entra al modelo, se monitorea)
    b = pred[["solicitud_id", *ATRIBUTOS]].merge(bio, on="solicitud_id")
    salida["falla_biometrica_primer_intento"] = {
        a: (b.groupby(a).fallo_primer_intento.mean() * 100).round(2).to_dict() for a in ("tramo_edad", "sector_laboral")}
    guardar_json(salida, ruta("reportes") / "equidad_resumen.json")
    for k in ("v1-base", "v1-base (mismo volumen que v2)", "v2-mitigado"):
        print(k, salida[k]["veredicto"], salida[k]["inclusion"])
    print("Biometría:", salida["falla_biometrica_primer_intento"])


def veredicto(r: pd.DataFrame) -> dict:
    return {
        "brecha_max_pp": round(float(r.brecha_aprobacion_pp.max()), 2),
        "atributo_peor": r.loc[r.brecha_aprobacion_pp.idxmax(), "atributo"],
        "dir_min": round(float(r.disparate_impact.min()), 3),
        "cumple_5pp": bool(r.cumple_5pp.all()),
        "cumple_80": bool(r.cumple_80.all()),
        "aprobado": bool(r.cumple_5pp.all() and r.cumple_80.all()),
    }


if __name__ == "__main__":
    main()
