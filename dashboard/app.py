"""AURORA SCORE · Panel de monitoreo (RF-11)

    streamlit run dashboard/app.py

Cuatro vistas: desempeño del modelo, drift (PSI/KS), equidad con semáforo contra 5 pp e
inclusión efectiva. Lee los resultados que deja `python src/pipeline.py` en reports/.
Datos 100 % sintéticos: caso ficticio con fines académicos.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from features import CATALOGO  # noqa: E402

REP = RAIZ / "reports"
AZUL, AZUL_CL, DORADO, ROJO, VERDE = "#4472C4", "#9DB4E3", "#E0A800", "#C0504D", "#2E8B57"
NOM = {"genero": "Género", "zona": "Zona", "tramo_edad": "Tramo de edad", "sector_laboral": "Sector laboral"}

st.set_page_config(page_title="AURORA SCORE · Monitoreo", page_icon="📊", layout="wide")


@st.cache_data
def leer(nombre):
    p = REP / nombre
    if p.suffix == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    if p.suffix == ".parquet":
        return pd.read_parquet(p)
    return pd.read_csv(p)


if not (REP / "metricas_modelos.json").exists():
    st.error("No hay resultados. Ejecute primero: `python src/pipeline.py`")
    st.stop()

met = leer("metricas_modelos.json")
eq = leer("equidad_resumen.json")
mon = leer("monitoreo_resumen.json")
lat = leer("latencia_resumen.json")
pred = leer("predicciones_test.parquet")
reg = json.loads((RAIZ / "models" / "registro_modelos.json").read_text(encoding="utf-8"))

st.markdown(
    f"""<div style="display:flex;align-items:center;gap:14px;margin-bottom:4px">
    <div style="width:14px;height:14px;background:{AZUL}"></div>
    <h2 style="margin:0">AURORA SCORE · Panel de monitoreo del modelo</h2></div>
    <div style="color:#6B7280;font-size:0.9rem">Vertex Financial Group · Prototipo Sprint 2 (fase F3) ·
    <b>datos sintéticos</b>, caso ficticio con fines académicos</div>""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Filtros")
    version = st.radio("Modelo", ["v2-mitigado", "v1-base"], index=0)
    paises = st.multiselect("País", sorted(pred.pais.unique()), default=sorted(pred.pais.unique()))
    st.divider()
    st.caption(f"Versión: **{version}**")
    st.caption(f"SHA-256: `{reg[version]['sha256'][:16]}…`")
    st.caption(f"Entrenado: {reg[version]['fecha_entrenamiento']}")
    st.caption(f"Variables: {reg[version]['n_variables']}")

tag = version.split("-")[0]
d = pred[pred.pais.isin(paises)].copy()
d["aprobado"] = d[f"aprobado_{tag}"]
d["pd"] = d[f"pd_{tag}"]
m = met["modelos"][version]

tab1, tab2, tab3, tab4 = st.tabs(["Desempeño del modelo", "Monitoreo de drift", "Equidad por grupo", "Inclusión efectiva"])

# ------------------------------------------------------------------ 1. desempeño
with tab1:
    c = st.columns(5)
    c[0].metric("AUC (mora real)", f"{m['auc_test_real']:.3f}")
    c[1].metric("KS", f"{m['ks_test_real']:.3f}")
    c[2].metric("Tasa de aprobación", f"{d.aprobado.mean():.1%}")
    c[3].metric("Mora de aprobados", f"{d[d.aprobado == 1].incumplio.mean():.2%}")
    c[4].metric("Latencia p95", f"{lat['p95_ms']:,.0f} ms".replace(",", "."), help="Límite RNF-01: 8.000 ms en el percentil 95")
    col1, col2 = st.columns(2)
    with col1:
        g = pd.DataFrame(m["curva_ganancia"])
        fig = go.Figure()
        fig.add_scatter(x=g.pct_poblacion * 100, y=g.pct_incumplidores_capturados * 100, mode="lines+markers",
                        line=dict(color=AZUL, width=3), name=version)
        fig.add_scatter(x=[0, 100], y=[0, 100], mode="lines", line=dict(color="#D1D5DB", dash="dash"), name="aleatorio")
        fig.update_layout(title="Curva de ganancia", xaxis_title="% solicitudes ordenadas por riesgo",
                          yaxis_title="% incumplidores capturados", height=380, margin=dict(t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        por_pais = d.groupby("pais").agg(aprobacion=("aprobado", "mean"), pd_media=("pd", "mean"),
                                         mora_aprobados=("incumplio", lambda s: s[d.loc[s.index, "aprobado"] == 1].mean()))
        fig = px.bar(por_pais.reset_index(), x="pais", y="aprobacion", text_auto=".1%", color_discrete_sequence=[AZUL],
                     title="Tasa de aprobación por país (umbral parametrizable)")
        fig.update_layout(height=380, yaxis_tickformat=".0%", margin=dict(t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    d["mora_si_aprobado"] = d.incumplio.where(d.aprobado == 1)
    mensual = d.groupby(d.fecha_solicitud.dt.to_period("M").astype(str)).agg(
        solicitudes=("aprobado", "size"), aprobacion=("aprobado", "mean"), mora_aprobados=("mora_si_aprobado", "mean"))
    mensual.index.name = "mes"
    st.dataframe(mensual.style.format({"aprobacion": "{:.1%}", "mora_aprobados": "{:.2%}"}), use_container_width=True)

# ------------------------------------------------------------------ 2. drift
with tab2:
    dr = leer("monitoreo_drift.csv")
    dr["descripcion"] = dr.variable.map(lambda v: CATALOGO[v][2])
    c = st.columns(3)
    c[0].metric("PSI del score", f"{mon['psi_score_total']:.4f}")
    c[1].metric("KS del score", f"{mon['ks_score_total']:.4f}")
    c[2].metric("Variables en alerta", sum(v for k, v in mon["variables_por_estado"].items() if k != "estable"))
    top = dr.head(15).iloc[::-1]
    colores = [ROJO if p > 0.25 else DORADO if p > 0.10 else AZUL for p in top.psi]
    fig = go.Figure(go.Bar(x=top.psi, y=top.descripcion, orientation="h", marker_color=colores))
    fig.add_vline(x=0.10, line_dash="dash", line_color=DORADO, annotation_text="vigilar")
    fig.add_vline(x=0.25, line_dash="dash", line_color=ROJO, annotation_text="crítico")
    fig.update_layout(title="PSI por variable: entrenamiento vs. cohorte reciente", height=480,
                      xaxis_range=[0, 0.3], margin=dict(t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pd.DataFrame(mon["score_mensual"]), use_container_width=True, hide_index=True)
    st.info("El PSI no detectó el sesgo de muestra: la diferencia de composición entre cohortes no alcanza a mover "
            "las distribuciones. Por eso la equidad se monitorea con métricas propias y no se infiere del drift.")

# ------------------------------------------------------------------ 3. equidad
with tab3:
    from fairness import metricas_por_grupo, resumen_brechas
    mg = metricas_por_grupo(d)
    rb = resumen_brechas(mg)
    c = st.columns(4)
    for col, (_, r) in zip(c, rb.iterrows()):
        ok = r.brecha_aprobacion_pp <= 5
        col.markdown(
            f"""<div style="border-radius:10px;padding:14px;background:{'#E8F5EE' if ok else '#FBEAEA'};
            border-left:6px solid {VERDE if ok else ROJO}">
            <div style="font-size:0.85rem;color:#4B5563">{NOM[r.atributo]}</div>
            <div style="font-size:1.8rem;font-weight:700">{r.brecha_aprobacion_pp:.1f} pp</div>
            <div style="font-size:0.8rem">{'🟢 cumple' if ok else '🔴 no cumple'} el límite de 5 pp ·
            DIR {r.disparate_impact:.2f}</div></div>""", unsafe_allow_html=True)
    st.write("")
    attr = st.selectbox("Atributo", list(NOM), format_func=NOM.get)
    g = mg[mg.atributo == attr]
    fig = go.Figure()
    fig.add_bar(x=g.grupo, y=g.tasa_aprobacion, name="Tasa de aprobación", marker_color=AZUL, text=g.tasa_aprobacion,
                texttemplate="%{text:.1%}")
    fig.add_bar(x=g.grupo, y=g.tpr_buenos_pagadores, name="Aprobación de buenos pagadores", marker_color=AZUL_CL,
                text=g.tpr_buenos_pagadores, texttemplate="%{text:.1%}")
    fig.add_scatter(x=g.grupo, y=g.incumplimiento_real, name="Mora real del grupo", mode="markers",
                    marker=dict(color=DORADO, size=14, symbol="diamond"))
    fig.update_layout(barmode="group", height=420, yaxis_tickformat=".0%", margin=dict(t=30, b=10),
                      title=f"{NOM[attr]}: aprobación vs. mora real")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Los atributos protegidos no son variables del modelo: se usan solo para esta auditoría.")

# ------------------------------------------------------------------ 4. inclusión
with tab4:
    sub = (d.zona == "rural") | (d.tramo_edad == "60+") | ((d.genero == "F") & (d.sector_laboral == "informal"))
    c = st.columns(3)
    c[0].metric("% de aprobados de grupos subrepresentados", f"{sub[d.aprobado == 1].mean():.1%}")
    c[1].metric("% de solicitantes de grupos subrepresentados", f"{sub.mean():.1%}")
    c[2].metric("Aprobación subrepresentados vs. resto",
                f"{d.aprobado[sub].mean():.1%} vs {d.aprobado[~sub].mean():.1%}")
    comp = pd.DataFrame([
        {"modelo": k, "grupos subrepresentados": v["inclusion"]["tasa_aprobacion_subrepresentados"] / 100,
         "resto": v["inclusion"]["tasa_aprobacion_resto"] / 100}
        for k, v in eq.items() if isinstance(v, dict) and "inclusion" in v])
    fig = px.bar(comp.melt("modelo", var_name="grupo", value_name="aprobación"), x="modelo", y="aprobación",
                 color="grupo", barmode="group", text_auto=".1%", color_discrete_sequence=[DORADO, AZUL],
                 title="Inclusión efectiva por versión del modelo (todos los países)")
    fig.update_layout(height=420, yaxis_tickformat=".0%", margin=dict(t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Grupos subrepresentados: población rural, mayores de 60 años y mujeres del sector informal.")
