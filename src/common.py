"""Utilidades compartidas: parámetros, rutas y semilla."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

RAIZ = Path(__file__).resolve().parents[1]


def cargar_params() -> dict:
    with open(RAIZ / "config" / "params.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


PARAMS = cargar_params()


def ruta(clave: str) -> Path:
    p = RAIZ / PARAMS["rutas"][clave]
    p.mkdir(parents=True, exist_ok=True)
    return p


def rng(offset: int = 0) -> np.random.Generator:
    return np.random.default_rng(PARAMS["semilla"] + offset)


def guardar_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


def leer_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))
