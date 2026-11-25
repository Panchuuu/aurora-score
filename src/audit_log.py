"""Registro de auditoría inmutable (RF-12, RNF-07).

Cada decisión se escribe como una línea JSON encadenada: el hash de cada registro incluye el
hash del anterior. Si alguien modifica, borra o reordena una línea, la verificación falla
desde ese punto. En producción esto se respalda en almacenamiento WORM; el prototipo
demuestra el mecanismo.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from common import ruta, guardar_json

GENESIS = "0" * 64


def _hash(prev: str, registro: dict) -> str:
    cuerpo = json.dumps(registro, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256((prev + cuerpo).encode("utf-8")).hexdigest()


class RegistroAuditoria:
    def __init__(self, path: Path):
        self.path = path
        self.ultimo = GENESIS
        if path.exists():
            with open(path, encoding="utf-8") as f:
                for linea in f:
                    self.ultimo = json.loads(linea)["hash"]

    def agregar(self, registro: dict) -> str:
        h = _hash(self.ultimo, registro)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"registro": registro, "hash_anterior": self.ultimo, "hash": h},
                               ensure_ascii=False, default=str) + "\n")
        self.ultimo = h
        return h

    def agregar_lote(self, registros: list[dict]) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            for r in registros:
                h = _hash(self.ultimo, r)
                f.write(json.dumps({"registro": r, "hash_anterior": self.ultimo, "hash": h},
                                   ensure_ascii=False, default=str) + "\n")
                self.ultimo = h


def verificar(path: Path) -> dict:
    prev = GENESIS
    with open(path, encoding="utf-8") as f:
        for n, linea in enumerate(f, 1):
            e = json.loads(linea)
            if e["hash_anterior"] != prev or _hash(prev, e["registro"]) != e["hash"]:
                return {"integro": False, "primera_linea_alterada": n}
            prev = e["hash"]
    return {"integro": True, "registros": n}


def main() -> None:
    import pandas as pd
    from train import cargar
    from decision import MotorDecision
    from explain import explicar_rechazos

    df = cargar()
    te = df[df.cohorte == "reciente"].reset_index(drop=True)
    motor = MotorDecision()
    dec = motor.decidir(te, te.pais)
    exp = explicar_rechazos(motor, te, dec).set_index("indice")

    path = ruta("auditoria") / "decisiones.jsonl"
    path.unlink(missing_ok=True)
    reg = RegistroAuditoria(path)
    registros = []
    for i in te.index:
        r = {"solicitud_id": int(te.at[i, "solicitud_id"]), "pais": te.at[i, "pais"],
             "fecha": str(te.at[i, "fecha_solicitud"].date()), "version_modelo": motor.version,
             "sha256_modelo": motor.sha256[:16], "pd": round(float(dec.at[i, "pd"]), 5),
             "umbral": float(dec.at[i, "umbral"]), "decision": "aprobado" if dec.at[i, "aprobado"] else "rechazado"}
        if i in exp.index:
            r["factores"] = [exp.at[i, c] for c in exp.columns if c.startswith("factor_") and pd.notna(exp.at[i, c])]
        registros.append(r)
    reg.agregar_lote(registros)

    ok = verificar(path)
    # Prueba de manipulación: se cambia una decisión en una copia y se verifica de nuevo
    copia = path.with_name("decisiones_manipulado.jsonl")
    shutil.copy(path, copia)
    lineas = copia.read_text(encoding="utf-8").splitlines()
    e = json.loads(lineas[499])
    e["registro"]["decision"] = "aprobado" if e["registro"]["decision"] == "rechazado" else "rechazado"
    lineas[499] = json.dumps(e, ensure_ascii=False)
    copia.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    manip = verificar(copia)
    copia.unlink()

    res = {"registros_escritos": len(registros), "verificacion_original": ok,
           "prueba_manipulacion_linea_500": manip}
    guardar_json(res, ruta("reportes") / "auditoria_integridad.json")
    print(res)


if __name__ == "__main__":
    main()
