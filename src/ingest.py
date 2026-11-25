"""Ingesta y consolidación multifuente (RF-01).

1. Lee las seis fuentes crudas.
2. Resuelve identidad por país (RF-02, ver identity.py).
3. Simula el rezago de 24-72 h de las fuentes 1, 2 y 3: un evento solo está disponible para
   decidir si ocurrió hace más horas que su rezago. Lo que todavía no llegó se excluye y se
   marca, igual que ocurriría en producción.
4. Escribe la capa consolidada en data/processed y un reporte de calidad.
"""
from __future__ import annotations

import pandas as pd

from common import ruta, guardar_json
import identity

FUENTES = ["solicitudes", "telecom_lineas", "telecom_actividad", "servicios", "marketplace",
           "app_metadatos", "redes_optin", "biometria"]
CON_REZAGO = ["telecom_actividad", "servicios", "marketplace"]


def main() -> None:
    raw, proc = ruta("raw"), ruta("processed")
    fuentes = {f: pd.read_parquet(raw / f"{f}.parquet") for f in FUENTES}
    solicitudes = fuentes.pop("solicitudes")

    enlazadas, calidad = identity.resolver(solicitudes, fuentes)

    frescura = []
    for nombre in CON_REZAGO:
        d = enlazadas[nombre]
        horas_desde_evento = d.dias_antes_solicitud * 24 + 12
        disponible = horas_desde_evento >= d.rezago_horas
        d["frescura_horas"] = (horas_desde_evento - d.rezago_horas).clip(lower=0)
        frescura.append({"fuente": nombre, "filas_enlazadas": len(d),
                         "no_disponibles_por_rezago": int((~disponible).sum()),
                         "pct_no_disponible": round(float((~disponible).mean()) * 100, 2),
                         "rezago_medio_h": round(float(d.rezago_horas.mean()), 1)})
        enlazadas[nombre] = d[disponible].reset_index(drop=True)

    solicitudes.drop(columns=["id_nacional", "telefono", "email"]).to_parquet(
        proc / "solicitudes.parquet", index=False)
    for nombre, d in enlazadas.items():
        d.to_parquet(proc / f"{nombre}.parquet", index=False)

    calidad.to_csv(ruta("reportes") / "calidad_identidad.csv", index=False)
    guardar_json({"identidad": calidad.to_dict("records"), "rezago": frescura},
                 ruta("reportes") / "calidad_ingesta.json")
    print(calidad.to_string(index=False))
    print(pd.DataFrame(frescura).to_string(index=False))


if __name__ == "__main__":
    main()
