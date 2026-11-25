"""Feature store precalculado (RF-01, RNF-01).

El score no se calcula leyendo las fuentes en el momento de la solicitud: las variables se
precalculan por solicitud y quedan en un feature store (parquet). En la ruta crítica de
decisión solo se LEE una fila, lo que es la base del argumento de los 8 segundos.

El caso describe más de 240 variables. El prototipo implementa un subconjunto representativo
(48) que cubre las seis fuentes y los tres tipos de señal (capacidad, comportamiento de
pago, huella digital). La lista completa con su origen está en CATALOGO.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import ruta, guardar_json

# nombre: (fuente, versión, texto para explicar el factor en lenguaje natural)
# versión: "ambos" | "base" (medición sin conciliar) | "mitigado" (conciliada / cobertura)
CATALOGO: dict[str, tuple[str, str, str]] = {
    # 1. Telecomunicaciones — línea
    "es_postpago": ("telecom", "ambos", "tipo de plan móvil"),
    "marca_telefono": ("telecom", "ambos", "marca del teléfono"),
    "gama_equipo": ("telecom", "ambos", "gama del equipo móvil"),
    "antiguedad_linea_meses": ("telecom", "ambos", "antigüedad de la línea móvil"),
    "comuna_antena": ("telecom", "ambos", "zona de la antena habitual"),
    "operador": ("telecom", "ambos", "operador móvil"),
    # 1. Telecomunicaciones — actividad
    "meses_telecom": ("telecom", "ambos", "número de meses con actividad móvil"),
    "recargas_media": ("telecom", "ambos", "número de recargas mensuales"),
    "recargas_regularidad": ("telecom", "ambos", "regularidad de las recargas"),
    "monto_recargas_medio": ("telecom", "ambos", "monto mensual de recargas"),
    "monto_recargas_tendencia": ("telecom", "ambos", "tendencia del gasto en recargas"),
    "datos_gb_medio": ("telecom", "ambos", "consumo de datos móviles"),
    "atraso_postpago_medio": ("telecom", "ambos", "atraso promedio en la cuenta postpago"),
    "atraso_postpago_max": ("telecom", "ambos", "atraso máximo en la cuenta postpago"),
    "meses_postpago_atraso": ("telecom", "ambos", "número de meses con atraso en la cuenta postpago"),
    # 2. Servicios básicos
    "n_servicios_titular": ("servicios", "ambos", "número de servicios básicos a su nombre"),
    "meses_servicios": ("servicios", "ambos", "número de meses con historial de servicios básicos"),
    "monto_servicios_medio": ("servicios", "ambos", "monto mensual de servicios básicos"),
    "pct_canal_corresponsal": ("servicios", "ambos", "uso de pago presencial en corresponsal"),
    "atraso_servicios_medio": ("servicios", "base", "atraso promedio en servicios básicos"),
    "atraso_servicios_max": ("servicios", "base", "atraso máximo en servicios básicos"),
    "pct_pagos_tardios": ("servicios", "base", "proporción de cuentas pagadas con atraso"),
    "pct_pagos_tardios_5d": ("servicios", "base", "proporción de cuentas con más de 5 días de atraso"),
    "atraso_servicios_medio_conc": ("servicios", "mitigado", "atraso promedio en servicios básicos"),
    "atraso_servicios_max_conc": ("servicios", "mitigado", "atraso máximo en servicios básicos"),
    "pct_pagos_tardios_conc": ("servicios", "mitigado", "proporción de cuentas pagadas con atraso"),
    "pct_pagos_tardios_5d_conc": ("servicios", "mitigado", "proporción de cuentas con más de 5 días de atraso"),
    # 3. Billeteras y marketplaces
    "meses_marketplace": ("marketplace", "ambos", "número de meses con compras en línea"),
    "compras_total": ("marketplace", "ambos", "número de compras en línea"),
    "compras_media": ("marketplace", "ambos", "promedio mensual de compras en línea"),
    "ticket_medio": ("marketplace", "ambos", "ticket promedio de compra"),
    "reclamos_total": ("marketplace", "ambos", "número de reclamos en compras en línea"),
    "devoluciones_total": ("marketplace", "ambos", "número de devoluciones en compras en línea"),
    "tasa_reclamos": ("marketplace", "ambos", "proporción de compras con reclamo"),
    "tasa_devoluciones": ("marketplace", "ambos", "proporción de compras devueltas"),
    "compras_tendencia": ("marketplace", "ambos", "tendencia de las compras en línea"),
    # 4. Metadatos de la app
    "tiempo_pantallas_seg": ("app", "ambos", "tiempo dedicado a revisar las condiciones"),
    "velocidad_formulario_seg": ("app", "ambos", "tiempo de llenado del formulario"),
    "n_ediciones_formulario": ("app", "ambos", "número de correcciones en el formulario"),
    "so_ios": ("app", "ambos", "sistema operativo del teléfono"),
    # 5. Redes sociales (opt-in, sin contenido)
    "redes_optin": ("redes", "ambos", "autorización de uso de redes sociales"),
    "antiguedad_cuenta_red": ("redes", "ambos", "antigüedad de la cuenta en redes"),
    "tamano_red_log": ("redes", "ambos", "tamaño de la red de contactos"),
    # Solicitud
    "monto_solicitado_usd": ("solicitud", "ambos", "monto solicitado"),
    "plazo_meses": ("solicitud", "ambos", "plazo solicitado"),
    "cuota_sobre_recarga": ("solicitud", "ambos", "cuota estimada frente al gasto móvil"),
    # Cobertura de datos (mitigación de exclusión digital inversa)
    "n_fuentes_con_datos": ("cobertura", "mitigado", "cantidad de fuentes con información"),
    "perfil_thin_file": ("cobertura", "mitigado", "historial digital limitado"),
}
CATEGORICAS = ["marca_telefono", "comuna_antena", "operador"]
GAMA = {"baja": 0, "media": 1, "alta": 2}


def _tendencia(df: pd.DataFrame, col: str) -> pd.Series:
    """Promedio de los 3 meses recientes menos los 3 anteriores."""
    rec = df[df.mes_rel >= -3].groupby("solicitud_id")[col].mean()
    ant = df[df.mes_rel < -3].groupby("solicitud_id")[col].mean()
    return (rec - ant).rename(f"{col}_tend")


def construir() -> pd.DataFrame:
    proc = ruta("processed")
    sol = pd.read_parquet(proc / "solicitudes.parquet")
    lin = pd.read_parquet(proc / "telecom_lineas.parquet")
    tel = pd.read_parquet(proc / "telecom_actividad.parquet")
    srv = pd.read_parquet(proc / "servicios.parquet")
    mk = pd.read_parquet(proc / "marketplace.parquet")
    app = pd.read_parquet(proc / "app_metadatos.parquet")
    red = pd.read_parquet(proc / "redes_optin.parquet")

    fs = sol[["solicitud_id", "pais", "fecha_solicitud", "cohorte", "monto_solicitado_usd", "plazo_meses"]].copy()

    l = lin.set_index("solicitud_id")
    fs = fs.join(pd.DataFrame({
        "es_postpago": (l.tipo_plan == "postpago").astype(int),
        "marca_telefono": l.marca_telefono, "gama_equipo": l.gama_equipo.map(GAMA),
        "antiguedad_linea_meses": l.antiguedad_linea_meses, "comuna_antena": l.comuna_antena,
        "operador": l.operador,
    }), on="solicitud_id")

    g = tel.groupby("solicitud_id")
    t = pd.DataFrame({
        "meses_telecom": g.size(),
        "recargas_media": g.n_recargas.mean(),
        "recargas_regularidad": 1 - (g.n_recargas.std() / (g.n_recargas.mean() + 1)).fillna(0),
        "monto_recargas_medio": g.monto_recargas.mean(),
        "datos_gb_medio": g.datos_gb.mean(),
        "atraso_postpago_medio": g.atraso_postpago_dias.mean(),
        "atraso_postpago_max": g.atraso_postpago_dias.max(),
        "meses_postpago_atraso": g.atraso_postpago_dias.apply(lambda s: (s > 0).sum() if s.notna().any() else np.nan),
    })
    t["monto_recargas_tendencia"] = _tendencia(tel, "monto_recargas")
    fs = fs.join(t, on="solicitud_id")

    g = srv.groupby("solicitud_id")
    s = pd.DataFrame({
        "n_servicios_titular": g.tipo_servicio.nunique(),
        "meses_servicios": g.mes_rel.nunique(),
        "monto_servicios_medio": g.monto.mean(),
        "pct_canal_corresponsal": g.canal_pago.apply(lambda c: (c == "corresponsal").mean()),
        "atraso_servicios_medio": g.dias_atraso_registrado.mean(),
        "atraso_servicios_max": g.dias_atraso_registrado.max(),
        "pct_pagos_tardios": g.dias_atraso_registrado.apply(lambda x: (x > 0).mean()),
        "pct_pagos_tardios_5d": g.dias_atraso_registrado.apply(lambda x: (x > 5).mean()),
        "atraso_servicios_medio_conc": g.fecha_pago_efectiva_dias_atraso.mean(),
        "atraso_servicios_max_conc": g.fecha_pago_efectiva_dias_atraso.max(),
        "pct_pagos_tardios_conc": g.fecha_pago_efectiva_dias_atraso.apply(lambda x: (x > 0).mean()),
        "pct_pagos_tardios_5d_conc": g.fecha_pago_efectiva_dias_atraso.apply(lambda x: (x > 5).mean()),
    })
    fs = fs.join(s, on="solicitud_id")

    g = mk.groupby("solicitud_id")
    m = pd.DataFrame({
        "meses_marketplace": g.size(),
        "compras_total": g.n_compras.sum(),
        "compras_media": g.n_compras.mean(),
        "ticket_medio": g.ticket_promedio.mean(),
        "reclamos_total": g.n_reclamos.sum(),
        "devoluciones_total": g.n_devoluciones.sum(),
    })
    m["tasa_reclamos"] = m.reclamos_total / m.compras_total.clip(lower=1)
    m["tasa_devoluciones"] = m.devoluciones_total / m.compras_total.clip(lower=1)
    m["compras_tendencia"] = _tendencia(mk, "n_compras")
    fs = fs.join(m, on="solicitud_id")
    for c in ("meses_marketplace", "compras_total", "compras_media", "reclamos_total", "devoluciones_total"):
        fs[c] = fs[c].fillna(0)

    a = app.set_index("solicitud_id")
    fs = fs.join(pd.DataFrame({
        "tiempo_pantallas_seg": a.tiempo_pantallas_seg, "velocidad_formulario_seg": a.velocidad_formulario_seg,
        "n_ediciones_formulario": a.n_ediciones_formulario, "so_ios": (a.sistema_operativo == "iOS").astype(int),
    }), on="solicitud_id")

    r = red.set_index("solicitud_id")
    fs = fs.join(pd.DataFrame({"antiguedad_cuenta_red": r.antiguedad_cuenta_meses,
                               "tamano_red_log": np.log1p(r.tamano_red)}), on="solicitud_id")
    fs["redes_optin"] = fs.antiguedad_cuenta_red.notna().astype(int)

    cuota = fs.monto_solicitado_usd * (1 + 0.031 * fs.plazo_meses) / fs.plazo_meses
    fs["cuota_sobre_recarga"] = cuota / fs.monto_recargas_medio.clip(lower=1)

    fs["meses_servicios"] = fs.meses_servicios.fillna(0)
    fs["n_servicios_titular"] = fs.n_servicios_titular.fillna(0)
    fs["n_fuentes_con_datos"] = ((fs.meses_telecom.fillna(0) >= 3).astype(int)
                                 + (fs.meses_servicios >= 3).astype(int)
                                 + (fs.meses_marketplace >= 3).astype(int) + fs.redes_optin)
    fs["perfil_thin_file"] = ((fs.antiguedad_linea_meses < 12) & (fs.meses_servicios < 3)).astype(int)

    for c in CATEGORICAS:
        fs[c] = fs[c].astype("category")
    return fs


def main() -> None:
    fs = construir()
    out = ruta("features")
    fs.to_parquet(out / "feature_store.parquet", index=False)
    guardar_json({k: {"fuente": v[0], "version": v[1], "descripcion": v[2]} for k, v in CATALOGO.items()},
                 out / "catalogo_variables.json")
    faltantes = set(CATALOGO) - set(fs.columns)
    assert not faltantes, faltantes
    # Control agregado tras la desviación D1 (llaves duplicadas generaban filas repetidas)
    assert fs.solicitud_id.is_unique, "El feature store tiene solicitudes duplicadas"
    print(f"Feature store: {len(fs):,} filas x {len(CATALOGO)} variables")


if __name__ == "__main__":
    main()
