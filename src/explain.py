"""Explicabilidad (RF-05): de 3 a 5 factores determinantes por rechazo, en lenguaje natural.

Usa TreeSHAP a través de `pred_contrib=True` de LightGBM, que calcula los valores SHAP
exactos del ensamble de árboles sin depender de una librería externa. Cada contribución es
el aporte de esa variable al log-odds de incumplimiento de la persona, respecto del promedio.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import PARAMS, ruta
from decision import MotorDecision
from features import CATALOGO

N_FACT = PARAMS["decision"]["n_factores_explicacion"]


def contribuciones(motor: MotorDecision, X: pd.DataFrame) -> pd.DataFrame:
    c = motor.booster.predict(X[motor.variables], pred_contrib=True)
    return pd.DataFrame(c[:, :-1], columns=motor.variables, index=X.index)


def _formato(v) -> str:
    if pd.isna(v):
        return "sin información"
    if isinstance(v, (float, np.floating)):
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(v)


FEMENINO = {"marca", "gama", "antigüedad", "zona", "regularidad", "tendencia", "proporción",
            "cantidad", "autorización", "cuota"}


def _con_articulo(desc: str) -> str:
    return ("la " if desc.split()[0] in FEMENINO else "el ") + desc


def factores(contrib: pd.Series, fila: pd.Series, referencia: pd.Series, n: int = N_FACT) -> list[str]:
    """Factores que más AUMENTARON el riesgo estimado de esta persona."""
    top = contrib[contrib > 0].sort_values(ascending=False).head(n)
    textos = []
    for var, _ in top.items():
        desc = _con_articulo(CATALOGO[var][2])
        v, ref = fila[var], referencia.get(var)
        if pd.isna(v):
            textos.append(f"No contamos con información sobre {desc}.")
        elif isinstance(ref, (int, float, np.number)) and not pd.isna(ref):
            if float(v) == float(ref):
                textos.append(f"{desc[0].upper() + desc[1:]} ({_formato(v)}) pesó en contra en la evaluación.")
                continue
            comp = "mayor" if float(v) > float(ref) else "menor"
            textos.append(f"{desc[0].upper() + desc[1:]} ({_formato(v)}) es {comp} que en las solicitudes "
                          f"aprobadas (mediana {_formato(ref)}).")
        else:
            textos.append(f"{desc[0].upper() + desc[1:]} ({_formato(v)}) se asocia a un riesgo mayor.")
    return textos


def explicar_rechazos(motor: MotorDecision, X: pd.DataFrame, decision: pd.DataFrame) -> pd.DataFrame:
    aprob = X[decision.aprobado == 1]
    ref = aprob[motor.variables].select_dtypes("number").median()
    rech = X[decision.aprobado == 0]
    C = contribuciones(motor, rech)
    filas = []
    for idx in rech.index:
        fs = factores(C.loc[idx], rech.loc[idx], ref)
        filas.append({"indice": idx, "n_factores": len(fs),
                      **{f"factor_{i+1}": t for i, t in enumerate(fs)}})
    return pd.DataFrame(filas)


def importancia_global(motor: MotorDecision, X: pd.DataFrame) -> pd.DataFrame:
    C = contribuciones(motor, X)
    return (C.abs().mean().sort_values(ascending=False)
            .rename("shap_medio_abs").reset_index().rename(columns={"index": "variable"}))


def main() -> None:
    from train import cargar
    df = cargar()
    te = df[df.cohorte == "reciente"].reset_index(drop=True)
    motor = MotorDecision()
    dec = motor.decidir(te, te.pais)
    exp = explicar_rechazos(motor, te, dec)
    exp.insert(0, "solicitud_id", te.loc[exp.indice, "solicitud_id"].to_numpy())
    exp.drop(columns="indice").to_csv(ruta("reportes") / "explicaciones_rechazos.csv", index=False, encoding="utf-8-sig")
    imp = importancia_global(motor, te)
    imp.to_csv(ruta("reportes") / "shap_importancia_global.csv", index=False)
    pct = (exp.n_factores >= 3).mean()
    print(f"Rechazos explicados: {len(exp):,} · con 3 a 5 factores: {pct:.1%}")
    print(exp.iloc[0].to_string())


if __name__ == "__main__":
    main()
