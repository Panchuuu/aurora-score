"""Motor de decisión con umbrales parametrizables por país (RF-04).

Carga el modelo desde el registro, verifica su hash antes de usarlo (RNF-09) y aplica el
umbral de probabilidad de incumplimiento definido para cada país en config/params.yaml.
"""
from __future__ import annotations

import hashlib

import lightgbm as lgb
import numpy as np
import pandas as pd

from common import PARAMS, ruta, leer_json


class MotorDecision:
    def __init__(self, version: str = "v2-mitigado"):
        reg = leer_json(ruta("modelos") / "registro_modelos.json")[version]
        path = ruta("modelos") / reg["archivo"]
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if sha != reg["sha256"]:
            raise RuntimeError(f"El modelo {version} no coincide con el hash registrado")
        self.version, self.sha256 = version, sha
        self.variables = reg["variables"]
        self.booster = lgb.Booster(model_file=str(path))
        self.umbrales = PARAMS["decision"]["umbral_pd"]

    def probabilidad(self, X: pd.DataFrame) -> np.ndarray:
        return self.booster.predict(X[self.variables])

    def decidir(self, X: pd.DataFrame, pais: pd.Series) -> pd.DataFrame:
        p = self.probabilidad(X)
        umbral = pais.map(self.umbrales).astype(float).to_numpy()
        return pd.DataFrame({"pd": p, "umbral": umbral, "aprobado": (p <= umbral).astype(int),
                             "version_modelo": self.version}, index=X.index)
