"""Resolución de identidad por país (RF-02).

Cada fuente identifica a la persona con una llave distinta y en formatos heterogéneos:
telecomunicaciones por número móvil, servicios básicos por RUT/DNI/CC/CURP del titular y
marketplaces por hash del correo. Este módulo normaliza las llaves por país y las enlaza con
la solicitud. Lo que no se puede enlazar se informa, no se descarta en silencio.
"""
from __future__ import annotations

import hashlib
import re

import pandas as pd


def _dv_rut(num: str) -> str:
    s, m = 0, 2
    for d in reversed(num):
        s += int(d) * m
        m = 2 if m == 7 else m + 1
    r = 11 - s % 11
    return "0" if r == 11 else "K" if r == 10 else str(r)


def normalizar_id_nacional(valor: str, pais: str | None = None) -> str | None:
    """Devuelve la forma canónica del identificador o None si es inválido."""
    if valor is None:
        return None
    v = re.sub(r"[.\s]", "", str(valor)).upper()
    if pais in (None, "CL") and re.fullmatch(r"\d{7,8}-?[\dK]", v):
        num, dv = v.replace("-", "")[:-1], v[-1]
        if _dv_rut(num) == dv:            # el dígito verificador detecta errores de digitación
            return f"{num}-{dv}"
        return None
    if pais == "CL":
        return None
    if re.fullmatch(r"[A-Z]{4}\d{6}[HM][A-Z]{5}\d{2}", v):      # CURP (MX)
        return v
    if re.fullmatch(r"\d{8,10}", v):                             # DNI (PE) / CC (CO)
        return v
    return None


def normalizar_telefono(valor: str) -> str | None:
    d = re.sub(r"\D", "", str(valor))
    if len(d) < 10:
        return None
    return "+" + d


def hash_email(valor: str) -> str:
    return hashlib.sha256(str(valor).strip().lower().encode()).hexdigest()


def resolver(solicitudes: pd.DataFrame, fuentes: dict[str, pd.DataFrame]) -> tuple[dict, pd.DataFrame]:
    """Agrega `solicitud_id` a cada fuente. Devuelve fuentes enlazadas y tabla de calidad."""
    s = solicitudes.copy()
    s["k_id"] = [normalizar_id_nacional(v, p) for v, p in zip(s.id_nacional, s.pais)]
    s["k_tel"] = s.telefono.map(normalizar_telefono)
    s["k_mail"] = s.email.map(hash_email)

    enlazadas, calidad = {}, []

    def _enlazar(nombre, df, col, fn, clave):
        d = df.copy()
        mapa = dict(zip(s[clave], s.solicitud_id))
        d["_k"] = [fn(v, mapa) for v in d[col]] if fn.__code__.co_argcount == 2 else d[col].map(fn)
        d["solicitud_id"] = d["_k"].map(mapa)
        ok = d.solicitud_id.notna()
        calidad.append({"fuente": nombre, "llave": col, "filas": len(d),
                        "enlazadas": int(ok.sum()), "tasa_enlace": round(float(ok.mean()), 4),
                        "invalidas": int(d["_k"].isna().sum())})
        enlazadas[nombre] = d[ok].drop(columns=["_k"]).assign(solicitud_id=lambda x: x.solicitud_id.astype(int))

    lineas = fuentes["telecom_lineas"]
    _enlazar("telecom_lineas", lineas, "numero_movil", normalizar_telefono, "k_tel")
    _enlazar("telecom_actividad", fuentes["telecom_actividad"], "numero_movil", normalizar_telefono, "k_tel")
    # En servicios el país no viene en la fuente: un mismo texto puede ser RUT sin guion o
    # DNI/CC. Se generan ambas lecturas candidatas y se usa la que existe en el padrón.
    def _llave_servicios(v, mapa):
        cands = [normalizar_id_nacional(v, "CL"), normalizar_id_nacional(v, "XX")]
        for c in cands:
            if c is not None and c in mapa:
                return c
        return next((c for c in cands if c is not None), None)

    _enlazar("servicios", fuentes["servicios"], "rut_dni_titular", _llave_servicios, "k_id")
    _enlazar("marketplace", fuentes["marketplace"], "email_sha256", lambda v: v, "k_mail")
    for nombre in ("app_metadatos", "redes_optin", "biometria"):
        enlazadas[nombre] = fuentes[nombre]
        calidad.append({"fuente": nombre, "llave": "solicitud_id", "filas": len(fuentes[nombre]),
                        "enlazadas": len(fuentes[nombre]), "tasa_enlace": 1.0, "invalidas": 0})
    return enlazadas, pd.DataFrame(calidad)
