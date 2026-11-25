"""Genera los documentos de gestión a partir de docs/tareas.csv y de los resultados.

* docs/tarjetas_trello.md   contenido exacto de cada tarjeta para copiar al tablero.
* docs/plan_vs_ejecucion.md tabla planificado vs. ejecutado y avance por paquete WBS.
* docs/model_card.md        ficha del modelo v2 desde el registro de modelos.
"""
from __future__ import annotations

import pandas as pd

from common import RAIZ, PARAMS, leer_json, ruta

DOCS = RAIZ / "docs"
SPRINTS = {"S1": "Sprint 1 · F2 Adquisición y comprensión de datos (03-11 al 14-11-2026)",
           "S2": "Sprint 2 · F3 Modelado (17-11 al 28-11-2026)",
           "S3": "Sprint 3 · F3 Modelado (backlog replanificado)"}
COLUMNA = {"Hecho": "Hecho", "Backlog": "Backlog", "En curso": "En curso", "En revisión": "En revisión"}


def tareas() -> pd.DataFrame:
    return pd.read_csv(DOCS / "tareas.csv", dtype=str).fillna("")


def tarjetas(t: pd.DataFrame) -> str:
    out = ["# Tablero Trello · AURORA SCORE — contenido de las tarjetas\n",
           "Columnas del tablero: **Backlog · Planificado Sprint · En curso · En revisión · Hecho**.\n",
           "Etiquetas sugeridas: `S1`, `S2`, `S3`, `WBS 1.x` a `WBS 6.x`, `Agregada` (control de cambios), "
           "`Desviación`.\n",
           "Cada tarjeta traza a un paquete de la WBS del EP3 y a un requerimiento (RF/RNF). Los commits del "
           "repositorio citan el id de la tarjeta (por ejemplo `AUR-14`).\n"]
    for s, d in t.groupby("sprint"):
        out.append(f"\n## {SPRINTS[s]}\n")
        for _, r in d.iterrows():
            etiquetas = [r.sprint, "WBS " + r.wbs.split()[0]]
            if r.origen.startswith("agregada"):
                etiquetas.append("Agregada")
            if r.desviacion:
                etiquetas.append("Desviación")
            out.append(f"### {r.id} · {r.titulo}\n")
            out.append(f"- **Columna:** {COLUMNA.get(r.estado, r.estado)}")
            out.append(f"- **Descripción:** {r.descripcion}")
            out.append(f"- **Paquete WBS:** {r.wbs}")
            out.append(f"- **Requerimiento:** {r.requerimiento}")
            out.append(f"- **Responsable:** {r.responsable}")
            out.append(f"- **Estimación:** {r.estimacion_h} h · **Real:** {r.real_h} h")
            out.append(f"- **Etiquetas:** {', '.join(etiquetas)}")
            if r.desviacion:
                out.append(f"- **Desviación:** {r.desviacion} (ver docs/desviaciones.md)")
            out.append(f"- **Evidencia:** `{r.evidencia}`")
            out.append(f"- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · "
                       f"[x] revisado por el otro integrante\n" if r.estado == "Hecho" else "")
    return "\n".join(out)


def plan_vs_ejecucion(t: pd.DataFrame) -> str:
    t = t.copy()
    t["est"], t["real"] = t.estimacion_h.astype(float), t.real_h.astype(float)
    t["desv_h"] = t.real - t.est
    t["desv_pct"] = (t.desv_h / t.est.where(t.est > 0)).mul(100)
    filas = ["| Tarjeta | Tarea | WBS | Resp. | Est. (h) | Real (h) | Estado | Desviación |",
             "|---|---|---|---|---:|---:|---|---|"]
    for _, r in t.iterrows():
        if r.est == 0:
            d = f"+{r.real:.0f} h (no planificada) {r.desviacion}"
        elif r.estado == "Backlog":
            d = f"replanificada a S3 {r.desviacion}"
        elif r.desv_h == 0:
            d = "—"
        else:
            d = f"{r.desv_h:+.0f} h ({r.desv_pct:+.0f} %) {r.desviacion}"
        filas.append(f"| {r.id} | {r.titulo} | {r.wbs.split()[0]} | {r.responsable.split()[0]} | "
                     f"{r.est:.0f} | {r.real:.0f} | {r.estado} | {d.strip()} |")

    res = []
    for s in ("S1", "S2"):
        d = t[t.sprint == s]
        res.append(f"| {s} | {len(d)} | {(d.estado == 'Hecho').sum()} | {d.est.sum():.0f} | {d.real.sum():.0f} | "
                   f"{(d.real.sum() / d.est.sum() - 1) * 100:+.1f} % |".replace(".", ","))
    sprint_tab = ["| Sprint | Tarjetas | Hechas | Est. (h) | Real (h) | Desviación de esfuerzo |",
                  "|---|---:|---:|---:|---:|---:|", *res]

    t["paquete"] = t.wbs.str.split(".").str[0] + ".0"
    nombres = {"1.0": "Gestión del proyecto", "2.0": "Gobernanza y cumplimiento", "3.0": "Plataforma de datos",
               "4.0": "Modelo analítico", "5.0": "Motor de decisión y agentes", "6.0": "Despliegue y expansión"}
    pk = ["| Paquete WBS | Tarjetas del corte | Hechas | Avance del corte |", "|---|---:|---:|---:|"]
    for p, d in t.groupby("paquete"):
        pk.append(f"| {p} {nombres[p]} | {len(d)} | {(d.estado == 'Hecho').sum()} | "
                  f"{(d.estado == 'Hecho').mean() * 100:.0f} % |")
    return "\n".join([
        "# Planificado vs. ejecutado — Sprint 1 y Sprint 2\n",
        "Corte del plan de 14 meses (EP3) que se ejecuta en este prototipo: fase **F2** (M2–M5) y comienzo de "
        "**F3** (M4–M8), en dos iteraciones de dos semanas, tal como define el plan. Datos sintéticos.\n",
        "Fuente única: `docs/tareas.csv`. Este documento se regenera con `python src/gestion.py`.\n",
        "## Resumen por sprint\n", *sprint_tab, "",
        "## Avance por paquete de la WBS (sobre las tarjetas de este corte)\n", *pk, "",
        "## Detalle por tarjeta\n", *filas, "",
        "Las horas reales son las registradas por el equipo en cada tarjeta al cerrarla.",
    ])


def model_card() -> str:
    reg = leer_json(ruta("modelos") / "registro_modelos.json")["v2-mitigado"]
    m = leer_json(ruta("reportes") / "metricas_modelos.json")
    e = leer_json(ruta("reportes") / "equidad_resumen.json")["v2-mitigado"]
    mv2 = m["modelos"]["v2-mitigado"]
    br = "\n".join(f"| {b['atributo']} | {b['grupo_min']} {b['aprob_min']:.1%} | {b['grupo_max']} {b['aprob_max']:.1%} | "
                   f"{b['brecha_aprobacion_pp']:.2f} | {b['disparate_impact']:.3f} |" for b in e["brechas"])
    return f"""# Model card · AURORA SCORE v2-mitigado

> Modelo entrenado con **datos sintéticos**. Caso ficticio con fines académicos (SCY1102, Duoc UC).

| Campo | Valor |
|---|---|
| Versión | v2-mitigado |
| Algoritmo | {reg['algoritmo']} |
| SHA-256 | `{reg['sha256']}` |
| Fecha de entrenamiento | {reg['fecha_entrenamiento']} |
| Variables | {reg['n_variables']} (subconjunto representativo de las más de 240 del caso) |
| Split | temporal: entrena {m['periodo_train'][0]} a {m['periodo_train'][1]} ({m['n_train']:,} solicitudes), evalúa {m['periodo_test'][0]} a {m['periodo_test'][1]} ({m['n_test']:,}) |
| Etiqueta | `incumplio` conciliado con la fecha efectiva de pago |
| Umbrales por país | {PARAMS['decision']['umbral_pd']} |

## Uso previsto
Estimar la probabilidad de incumplimiento de solicitantes sin historial en burós, para créditos de consumo
digital de VFG en Chile y Perú durante el piloto ampliado. **No** está validado para Colombia ni México hasta
cumplir el hito de decisión de M11, ni para otros productos de crédito.

## Desempeño (cohorte reciente, mora real)
| Métrica | Valor |
|---|---|
| AUC-ROC | {mv2['auc_test_real']} |
| KS | {mv2['ks_test_real']} |
| AUC en entrenamiento | {mv2['auc_train']} |
| Tasa de aprobación | {mv2['tasa_aprobacion']:.1%} |
| Mora de aprobados | {mv2['mora_aprobados']:.2%} |
| Mora de rechazados | {mv2['mora_rechazados']:.2%} |

## Equidad (criterio del plan: brecha ≤ 5 pp y regla del 80 %)
| Atributo | Grupo con menor aprobación | Grupo con mayor aprobación | Brecha (pp) | Disparate impact |
|---|---|---|---:|---:|
{br}

Veredicto: **{'cumple' if e['veredicto']['aprobado'] else 'no cumple'}**. Los atributos protegidos no son variables del modelo.

## Medidas de mitigación aplicadas
1. Conciliación de atraso y mora con la fecha efectiva de pago (sesgo de medición).
2. Eliminación de variables con correlación > 0,35 con un atributo protegido: {', '.join(m['proxies_eliminadas'])}.
3. Reponderación de la cohorte histórica a la composición de la población objetivo y variables de cobertura de datos.

## Limitaciones conocidas
- Datos sintéticos: las cifras demuestran el mecanismo, no el desempeño esperado con datos reales.
- No incluye *reject inference*: el sesgo de retroalimentación (solo se observa el pago de los aprobados) queda pendiente (AUR-24).
- La validación del supuesto de mora exige 12 meses de comportamiento observado (condición 3 del directorio).
- Cada rechazo se explica con 3 a 5 factores TreeSHAP; la carta final requiere revisión legal por país.
"""


def main() -> None:
    t = tareas()
    (DOCS / "tarjetas_trello.md").write_text(tarjetas(t), encoding="utf-8")
    (DOCS / "plan_vs_ejecucion.md").write_text(plan_vs_ejecucion(t), encoding="utf-8")
    (DOCS / "model_card.md").write_text(model_card(), encoding="utf-8")
    print("Documentos de gestión generados en docs/")


if __name__ == "__main__":
    main()
