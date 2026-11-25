"""Genera los gráficos de reports/figures a partir de los resultados del pipeline."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

from common import ruta, leer_json

AZUL, AZUL_CL, DORADO, GRIS, TINTA, ROJO = "#4472C4", "#9DB4E3", "#E0A800", "#6B7280", "#111111", "#C0504D"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": "#9CA3AF", "axes.titleweight": "bold",
                     "axes.titlesize": 13, "figure.dpi": 150, "savefig.bbox": "tight"})
FIG = ruta("figuras")
REP = ruta("reportes")
NOM = {"genero": "Género", "zona": "Zona", "tramo_edad": "Tramo de edad", "sector_laboral": "Sector laboral"}


def _guardar(fig, nombre):
    fig.savefig(FIG / nombre, facecolor="white")
    plt.close(fig)


def composicion():
    r = leer_json(REP / "resumen_generador.json")["composicion"]
    items = [("zona", "rural"), ("genero", "F"), ("tramo_edad", "60+"), ("sector_laboral", "informal")]
    etiq = ["Rural", "Mujeres", "60 años o más", "Sector informal"]
    h = [r[a]["historica"].get(g, 0) * 100 for a, g in items]
    c = [r[a]["reciente"].get(g, 0) * 100 for a, g in items]
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    x = np.arange(len(items))
    ax.bar(x - 0.2, h, 0.4, color=GRIS, label="Cohorte histórica (entrenamiento)")
    ax.bar(x + 0.2, c, 0.4, color=AZUL, label="Cohorte reciente (población objetivo)")
    for i in range(len(x)):
        ax.text(x[i] - 0.2, h[i] + 1, f"{h[i]:.1f}%", ha="center", fontsize=9)
        ax.text(x[i] + 0.2, c[i] + 1, f"{c[i]:.1f}%", ha="center", fontsize=9)
    ax.set_xticks(x, etiq); ax.set_ylabel("% de solicitudes"); ax.set_ylim(0, max(c + h) * 1.25)
    ax.legend(frameon=False, fontsize=9); ax.set_title("Sesgo de muestra: grupos subrepresentados")
    _guardar(fig, "01_sesgo_muestra.png")


def medicion():
    r = leer_json(REP / "resumen_generador.json")
    a = ["zona", "sector_laboral", "tramo_edad"]
    filas = [(f"{NOM[k]}: {g}", r["incumplio_real_por_grupo"][k][g] * 100, r["incumplio_registrado_por_grupo"][k][g] * 100)
             for k in a for g in r["incumplio_real_por_grupo"][k]]
    fig, ax = plt.subplots(figsize=(7.5, 4))
    y = np.arange(len(filas))
    ax.barh(y + 0.2, [f[1] for f in filas], 0.4, color=AZUL, label="Mora real (conciliada)")
    ax.barh(y - 0.2, [f[2] for f in filas], 0.4, color=DORADO, label="Mora registrada por el sistema")
    ax.set_yticks(y, [f[0] for f in filas], fontsize=9); ax.invert_yaxis()
    ax.set_xlabel("% de créditos"); ax.set_xlim(0, 30); ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_title("Sesgo de medición: la mora registrada no es la real")
    _guardar(fig, "02_sesgo_medicion.png")


def roc_y_ganancia():
    p = pd.read_parquet(REP / "predicciones_test.parquet")
    m = leer_json(REP / "metricas_modelos.json")["modelos"]
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    for col, nom, color in (("pd_v1", "v1-base", GRIS), ("pd_v2", "v2-mitigado", AZUL)):
        fpr, tpr, _ = roc_curve(p.incumplio, p[col])
        axs[0].plot(fpr, tpr, color=color, lw=2, label=f"{nom} · AUC {m[nom]['auc_test_real']:.3f}")
        g = pd.DataFrame(m[nom]["curva_ganancia"])
        axs[1].plot(g.pct_poblacion * 100, g.pct_incumplidores_capturados * 100, color=color, lw=2, marker="o", ms=3, label=nom)
    axs[0].plot([0, 1], [0, 1], ls="--", color="#D1D5DB")
    axs[0].set_xlabel("Tasa de falsos positivos"); axs[0].set_ylabel("Tasa de verdaderos positivos")
    axs[0].set_title("Curva ROC (cohorte reciente)"); axs[0].legend(frameon=False, fontsize=9, loc="lower right")
    axs[1].plot([0, 100], [0, 100], ls="--", color="#D1D5DB")
    axs[1].set_xlabel("% de solicitudes ordenadas por riesgo"); axs[1].set_ylabel("% de incumplidores capturados")
    axs[1].set_title("Curva de ganancia"); axs[1].legend(frameon=False, fontsize=9, loc="lower right")
    _guardar(fig, "03_roc_ganancia.png")


def equidad():
    e = leer_json(REP / "equidad_resumen.json")
    attrs = ["genero", "zona", "tramo_edad", "sector_laboral"]
    v1 = {b["atributo"]: b["brecha_aprobacion_pp"] for b in e["v1-base"]["brechas"]}
    v1v = {b["atributo"]: b["brecha_aprobacion_pp"] for b in e["v1-base (mismo volumen que v2)"]["brechas"]}
    v2 = {b["atributo"]: b["brecha_aprobacion_pp"] for b in e["v2-mitigado"]["brechas"]}
    fig, ax = plt.subplots(figsize=(8, 3.8))
    x = np.arange(len(attrs))
    for off, d, c, l in ((-0.27, v1, GRIS, "v1-base (umbral del plan)"), (0, v1v, AZUL_CL, "v1-base (mismo volumen que v2)"),
                         (0.27, v2, AZUL, "v2-mitigado")):
        vals = [d[a] for a in attrs]
        ax.bar(x + off, vals, 0.27, color=c, label=l)
        for xi, v in zip(x + off, vals):
            ax.text(xi, v + 0.4, f"{v:.1f}", ha="center", fontsize=8.5)
    ax.axhline(5, color=ROJO, ls="--", lw=1.5); ax.text(3.45, 5.4, "límite 5 pp", color=ROJO, fontsize=9, ha="right")
    ax.set_xticks(x, [NOM[a] for a in attrs]); ax.set_ylabel("Brecha de aprobación (pp)")
    ax.legend(frameon=False, fontsize=9); ax.set_title("Auditoría de equidad: brecha máxima entre grupos")
    _guardar(fig, "04_equidad_brechas.png")

    g = pd.read_csv(REP / "equidad_por_grupo.csv")
    g = g[g.modelo.isin(["v1-base (mismo volumen que v2)", "v2-mitigado"])]
    fig, axs = plt.subplots(1, 4, figsize=(12, 3.4), sharey=True)
    for ax, a in zip(axs, attrs):
        d = g[g.atributo == a]
        grupos = sorted(d.grupo.unique())
        x = np.arange(len(grupos))
        for off, mod, c in ((-0.2, "v1-base (mismo volumen que v2)", AZUL_CL), (0.2, "v2-mitigado", AZUL)):
            dd = d[d.modelo == mod].set_index("grupo").reindex(grupos)
            ax.bar(x + off, dd.tasa_aprobacion * 100, 0.4, color=c, label=mod)
        ax.set_xticks(x, grupos, fontsize=9); ax.set_title(NOM[a], fontsize=11)
        ax.set_ylim(50, 85)
    axs[0].set_ylabel("Tasa de aprobación (%)"); h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, frameon=False, fontsize=9, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.07))
    _guardar(fig, "05_aprobacion_por_grupo.png")


def ablacion():
    a = pd.read_csv(REP / "ablacion_mitigacion.csv")
    fig, ax1 = plt.subplots(figsize=(8.5, 3.8))
    x = np.arange(len(a))
    cols = [ROJO if not c else AZUL for c in a.cumple]
    ax1.bar(x, a.brecha_max_pp, color=cols, width=0.55)
    for xi, v in zip(x, a.brecha_max_pp):
        ax1.text(xi, v + 0.3, f"{v:.1f} pp", ha="center", fontsize=9)
    ax1.axhline(5, color=ROJO, ls="--", lw=1.2)
    ax1.set_ylabel("Brecha máxima (pp)"); ax1.set_xticks(x, [p.split(". ", 1)[1].replace("+ ", "+ ").replace(" de ", "\nde ", 1).replace(" y ", "\ny ", 1) for p in a.paso], fontsize=8.5)
    ax2 = ax1.twinx(); ax2.plot(x, a.auc_test_real, color=DORADO, marker="o", lw=2)
    for xi, v in zip(x, a.auc_test_real):
        ax2.text(xi + 0.1, v - 0.008, f"{v:.3f}", fontsize=9, color="#B7891B", fontweight="bold")
    ax2.set_ylabel("AUC (mora real)", color="#B7891B"); ax2.set_ylim(0.70, 0.84); ax2.spines["top"].set_visible(False)
    ax1.set_title("Ciclo de mitigación: aporte de cada medida (a igual volumen)")
    _guardar(fig, "06_ablacion.png")


def shap_global():
    from features import CATALOGO
    s = pd.read_csv(REP / "shap_importancia_global.csv").head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.barh([CATALOGO[v][2] for v in s.variable], s.shap_medio_abs, color=AZUL)
    ax.set_xlabel("|SHAP| medio (log-odds)"); ax.tick_params(axis="y", labelsize=8.5)
    ax.set_title("Explicabilidad global del modelo v2 (TreeSHAP)")
    _guardar(fig, "07_shap_global.png")


def latencia():
    d = pd.read_csv(REP / "latencia_mediciones.csv")
    r = leer_json(REP / "latencia_resumen.json")
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1.3, 1]})
    axs[0].hist(d.total, bins=50, color=AZUL)
    axs[0].axvline(r["p95_ms"], color=DORADO, lw=2); axs[0].text(r["p95_ms"] + 60, axs[0].get_ylim()[1] * 0.9, f"p95 = {r['p95_ms']:.0f} ms", color="#B7891B", fontsize=9)
    axs[0].axvline(8000, color=ROJO, ls="--", lw=1.5); axs[0].text(7900, axs[0].get_ylim()[1] * 0.9, "límite 8.000 ms", color=ROJO, ha="right", fontsize=9)
    axs[0].set_xlim(0, 8400); axs[0].set_xlabel("Latencia total por solicitud (ms)"); axs[0].set_ylabel("Solicitudes")
    axs[0].set_title(f"Ruta crítica de decisión · {r['n_solicitudes']:,} solicitudes".replace(",", "."))
    comp = r["p95_por_componente_ms"]
    NC = {"recepcion": "recepción", "feature_store": "feature store", "variables_al_vuelo": "variables al vuelo", "terceros": "terceros (timeout 1,5 s)"}; nom = [NC.get(k.split("_", 1)[1], k.split("_", 1)[1]) for k in comp]
    colors = [DORADO if any(s in k for s in ("recepcion", "feature_store", "terceros", "respuesta")) else AZUL for k in comp]
    axs[1].barh(nom[::-1], list(comp.values())[::-1], color=colors[::-1])
    axs[1].set_xlabel("p95 por componente (ms)"); axs[1].set_title("Dónde se va el tiempo")
    axs[1].tick_params(axis="y", labelsize=9)
    axs[1].text(0.98, 0.02, "dorado: incluye red/E-S simulada\nazul: cómputo medido", transform=axs[1].transAxes,
                ha="right", va="bottom", fontsize=8, color=GRIS)
    _guardar(fig, "08_latencia.png")


def drift():
    from features import CATALOGO
    t = pd.read_csv(REP / "monitoreo_drift.csv").head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.barh([CATALOGO[v][2] for v in t.variable], t.psi, color=AZUL)
    ax.axvline(0.10, color=DORADO, ls="--", lw=1.2); ax.axvline(0.25, color=ROJO, ls="--", lw=1.2)
    ax.text(0.102, -0.9, "vigilar", color="#B7891B", fontsize=8.5); ax.text(0.252, -0.9, "crítico", color=ROJO, fontsize=8.5)
    ax.set_xlim(0, 0.28); ax.set_xlabel("PSI entrenamiento vs. cohorte reciente"); ax.tick_params(axis="y", labelsize=8.5)
    ax.set_title("Monitoreo de drift (12 variables con mayor PSI)")
    _guardar(fig, "09_drift_psi.png")


def gestion():
    t = pd.read_csv(ruta("reportes").parent / "docs" / "tareas.csv")
    t = t[t.sprint.isin(["S1", "S2"])]
    fig, ax = plt.subplots(figsize=(10, 4.4))
    x = np.arange(len(t))
    ax.bar(x - 0.2, t.estimacion_h, 0.4, color=AZUL_CL, label="Estimado (h)")
    ax.bar(x + 0.2, t.real_h, 0.4, color=[ROJO if r > e else AZUL for r, e in zip(t.real_h, t.estimacion_h)], label="Real (h)")
    ax.set_xticks(x, t.id, rotation=90, fontsize=8); ax.set_ylabel("Horas")
    ax.axvline(t.sprint.eq("S1").sum() - 0.5, color=GRIS, ls=":", lw=1)
    ax.text(0, ax.get_ylim()[1] * 0.95, "Sprint 1 · F2", fontsize=9, color=GRIS)
    ax.text(t.sprint.eq("S1").sum(), ax.get_ylim()[1] * 0.95, "Sprint 2 · F3", fontsize=9, color=GRIS)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    ax.set_title("Planificado vs. ejecutado por tarjeta (rojo: sobre lo estimado)")
    _guardar(fig, "10_plan_vs_ejecutado.png")


def main():
    for f in (composicion, medicion, roc_y_ganancia, equidad, ablacion, shap_global, latencia, drift):
        f()
    if (ruta("reportes").parent / "docs" / "tareas.csv").exists():
        gestion()
    print("Figuras en", FIG)


if __name__ == "__main__":
    main()
