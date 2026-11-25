"""Entrenamiento del modelo de scoring (RF-03) y ciclo de mitigación de sesgo.

Se entrenan dos versiones con el mismo algoritmo (LightGBM, ensamble de gradient boosting):

* v1-base: lo que haría un equipo sin control de sesgo. Usa todas las variables, el atraso
  tal como lo registran las fuentes y la mora tal como la registró el sistema histórico.
* v2-mitigado: aplica tres medidas, una por cada foco de sesgo que la auditoría detecta:
    1. Sesgo de medición  -> concilia atraso y mora con la fecha efectiva de pago.
    2. Variables proxy    -> elimina las variables con correlación > 0,35 con un atributo protegido.
    3. Sesgo de muestra   -> repondera la cohorte histórica a la composición de la población
                             objetivo; agrega variables de cobertura para separar
                             "sin datos" de "mal pagador" (exclusión digital inversa).

Split temporal, no aleatorio: entrena con solicitudes hasta el 30-09-2025 (cohorte
histórica) y evalúa con octubre a diciembre de 2025 (cohorte reciente).
"""
from __future__ import annotations

import hashlib
from datetime import datetime

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix

from common import PARAMS, ruta, guardar_json, leer_json
from features import CATALOGO, CATEGORICAS
import fairness

ATR = fairness.ATRIBUTOS


def cargar() -> pd.DataFrame:
    fs = pd.read_parquet(ruta("features") / "feature_store.parquet")
    raw = ruta("raw")
    prot = pd.read_parquet(raw / "atributos_protegidos.parquet")
    res = pd.read_parquet(raw / "resultados.parquet")
    return fs.merge(prot, on="solicitud_id").merge(res, on="solicitud_id")


def ks(y, p) -> float:
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.max(tpr - fpr))


def pesos_reponderacion(train: pd.DataFrame, objetivo: pd.DataFrame) -> np.ndarray:
    celda = lambda d: d[ATR].astype(str).agg("|".join, axis=1)
    c_tr, c_obj = celda(train), celda(objetivo)
    p_tr = c_tr.value_counts(normalize=True)
    p_obj = c_obj.value_counts(normalize=True)
    w = (c_tr.map(p_obj) / c_tr.map(p_tr)).fillna(1.0).clip(0.2, 8.0)
    return (w / w.mean()).to_numpy()


def entrenar(X, y, w=None, fechas=None):
    """Early stopping con validación temporal: el último mes del período de entrenamiento
    se usa para fijar el número de árboles y luego se reentrena con todo el período."""
    cats = [c for c in CATEGORICAS if c in X.columns]
    params = dict(PARAMS["modelo"]["params"])
    if fechas is not None:
        val = (fechas >= fechas.max() - pd.Timedelta(days=30)).to_numpy()
        m = lgb.LGBMClassifier(random_state=PARAMS["semilla"], **{**params, "n_estimators": 2000})
        m.fit(X[~val], y[~val], sample_weight=None if w is None else w[~val],
              eval_X=(X[val],), eval_y=(y[val],), eval_metric="auc", categorical_feature=cats,
              callbacks=[lgb.early_stopping(100, verbose=False)])
        params["n_estimators"] = max(50, int(m.best_iteration_))
    m = lgb.LGBMClassifier(random_state=PARAMS["semilla"], **params)
    m.fit(X, y, sample_weight=w, categorical_feature=cats)
    return m


def registrar(modelo, version: str, variables: list[str], extra: dict) -> dict:
    d = ruta("modelos")
    path = d / f"aurora_score_{version}.txt"
    modelo.booster_.save_model(str(path))
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    reg_path = d / "registro_modelos.json"
    registro = leer_json(reg_path) if reg_path.exists() else {}
    registro[version] = {"archivo": path.name, "sha256": sha,
                         "fecha_entrenamiento": datetime.now().isoformat(timespec="seconds"),
                         "algoritmo": "LightGBM (gradient boosting)",
                         "n_variables": len(variables), "variables": variables, **extra}
    guardar_json(registro, reg_path)
    return registro[version]


def decidir(pd_: np.ndarray, pais: pd.Series) -> np.ndarray:
    umbral = pais.map(PARAMS["decision"]["umbral_pd"]).astype(float).to_numpy()
    return (pd_ <= umbral).astype(int)


def curva_ganancia(y, p, n=20):
    orden = np.argsort(-p)
    y = np.asarray(y)[orden]
    cortes = np.linspace(0, 1, n + 1)
    return [{"pct_poblacion": round(c, 3),
             "pct_incumplidores_capturados": round(float(y[: int(c * len(y))].sum() / y.sum()), 4)}
            for c in cortes]


def main() -> None:
    df = cargar()
    corte = pd.Timestamp(PARAMS["split_temporal"]["corte_entrenamiento"])
    tr = df[df.fecha_solicitud <= corte].reset_index(drop=True)
    te = df[df.fecha_solicitud > corte].reset_index(drop=True)

    vars_base = [k for k, v in CATALOGO.items() if v[1] in ("ambos", "base")]
    vars_mit_cand = [k for k, v in CATALOGO.items() if v[1] in ("ambos", "mitigado")]

    # ---- v1-base
    m1 = entrenar(tr[vars_base], tr.incumplio_registrado, fechas=tr.fecha_solicitud)

    # ---- detección de proxies sobre la cohorte histórica
    corr = fairness.correlacion_proxies(tr[vars_mit_cand], tr[ATR])
    corr.to_csv(ruta("reportes") / "correlacion_proxies.csv")
    proxies = corr[corr.es_proxy].index.tolist()
    # las variables de cobertura se conservan: describen ausencia de datos, no al grupo
    proxies = [p for p in proxies if CATALOGO[p][0] != "cobertura"]
    vars_mit = [v for v in vars_mit_cand if v not in proxies]

    # ---- v2-mitigado
    w = pesos_reponderacion(tr, te)     # composición objetivo: solicitantes recientes (sin etiqueta)
    m2 = entrenar(tr[vars_mit], tr.incumplio, w, fechas=tr.fecha_solicitud)

    salida = {"n_train": len(tr), "n_test": len(te),
              "periodo_train": [str(tr.fecha_solicitud.min().date()), str(tr.fecha_solicitud.max().date())],
              "periodo_test": [str(te.fecha_solicitud.min().date()), str(te.fecha_solicitud.max().date())],
              "proxies_eliminadas": proxies, "modelos": {}}

    pred = te[["solicitud_id", "pais", "fecha_solicitud", "incumplio", "incumplio_registrado", *ATR]].copy()
    for nombre, modelo, vars_, etiqueta in (("v1-base", m1, vars_base, "incumplio_registrado"),
                                            ("v2-mitigado", m2, vars_mit, "incumplio")):
        p = modelo.predict_proba(te[vars_])[:, 1]
        p_tr = modelo.predict_proba(tr[vars_])[:, 1]
        apr = decidir(p, te.pais)
        tag = nombre.split("-")[0]
        pred[f"pd_{tag}"], pred[f"aprobado_{tag}"] = p, apr
        tn, fp, fn, tp = confusion_matrix(te.incumplio, 1 - apr).ravel()  # positivo = rechazo
        met = {
            "etiqueta_entrenamiento": etiqueta,
            "auc_test_real": round(roc_auc_score(te.incumplio, p), 4),
            "ks_test_real": round(ks(te.incumplio, p), 4),
            "auc_test_registrada": round(roc_auc_score(te.incumplio_registrado, p), 4),
            "auc_train": round(roc_auc_score(tr[etiqueta], p_tr), 4),
            "tasa_aprobacion": round(float(apr.mean()), 4),
            "mora_aprobados": round(float(te.incumplio[apr == 1].mean()), 4),
            "mora_rechazados": round(float(te.incumplio[apr == 0].mean()), 4),
            "matriz_confusion": {"rechaza_y_incumple": int(tp), "rechaza_y_paga": int(fp),
                                 "aprueba_e_incumple": int(fn), "aprueba_y_paga": int(tn)},
            "curva_ganancia": curva_ganancia(te.incumplio, p),
        }
        info = registrar(modelo, nombre, vars_, {"metricas": {k: v for k, v in met.items() if k != "curva_ganancia"},
                                                  "split": "temporal", "corte": str(corte.date())})
        met["sha256"] = info["sha256"]
        salida["modelos"][nombre] = met

    # Comparación a igual volumen: umbral de v1 ajustado por país para aprobar lo mismo que v2
    pred["aprobado_v1_mismo_volumen"] = 0
    for pais, d in pred.groupby("pais"):
        q = d.aprobado_v2.mean()
        corte_pd = np.quantile(d.pd_v1, q)
        pred.loc[d.index, "aprobado_v1_mismo_volumen"] = (d.pd_v1 <= corte_pd).astype(int)

    # ---- Ablación: aporte de cada medida de mitigación, acumulativa, a igual volumen de aprobación
    vars_conc = [k for k, v in CATALOGO.items() if v[1] == "ambos"] + \
                [k for k, v in CATALOGO.items() if v[1] == "mitigado" and CATALOGO[k][0] != "cobertura"]
    vars_conc_sin_proxy = [v for v in vars_conc if v not in proxies]
    pasos = [
        ("0. Base (v1)", vars_base, "incumplio_registrado", None),
        ("1. + conciliación de atraso y mora", vars_conc, "incumplio", None),
        ("2. + eliminación de proxies", vars_conc_sin_proxy, "incumplio", None),
        ("3. + reponderación y cobertura (v2)", vars_mit, "incumplio", w),
    ]
    abl = []
    for nombre, vars_, etiqueta, pesos in pasos:
        m = entrenar(tr[vars_], tr[etiqueta], pesos, fechas=tr.fecha_solicitud)
        p = m.predict_proba(te[vars_])[:, 1]
        apr = np.zeros(len(te), dtype=int)
        for pais, idx in te.groupby("pais").groups.items():
            q = pred.loc[idx, "aprobado_v2"].mean()
            apr[idx] = (p[idx] <= np.quantile(p[idx], q)).astype(int)
        d = te[[*ATR, "incumplio"]].assign(aprobado=apr)
        v = fairness.veredicto(fairness.resumen_brechas(fairness.metricas_por_grupo(d)))
        abl.append({"paso": nombre, "auc_test_real": round(roc_auc_score(te.incumplio, p), 4),
                    "brecha_max_pp": v["brecha_max_pp"], "atributo_peor": v["atributo_peor"],
                    "dir_min": v["dir_min"], "cumple": v["aprobado"]})
    pd.DataFrame(abl).to_csv(ruta("reportes") / "ablacion_mitigacion.csv", index=False)
    salida["ablacion"] = abl
    print(pd.DataFrame(abl).to_string(index=False))

    imp = pd.DataFrame({"variable": vars_mit, "importancia_gain": m2.booster_.feature_importance("gain")})
    imp.sort_values("importancia_gain", ascending=False).to_csv(ruta("reportes") / "importancia_v2.csv", index=False)
    imp1 = pd.DataFrame({"variable": vars_base, "importancia_gain": m1.booster_.feature_importance("gain")})
    imp1.sort_values("importancia_gain", ascending=False).to_csv(ruta("reportes") / "importancia_v1.csv", index=False)

    pred.to_parquet(ruta("reportes") / "predicciones_test.parquet", index=False)
    guardar_json(salida, ruta("reportes") / "metricas_modelos.json")
    for k, v in salida["modelos"].items():
        print(k, {x: v[x] for x in ("auc_test_real", "ks_test_real", "tasa_aprobacion", "mora_aprobados")})
    print("Proxies eliminadas:", proxies)


if __name__ == "__main__":
    main()
