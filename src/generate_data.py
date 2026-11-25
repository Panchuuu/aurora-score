"""Generador sintético de las seis fuentes de AURORA SCORE.

Todo lo que produce este script es ficticio. Los datos reproducen la ESTRUCTURA y los
SESGOS documentados en el informe de factibilidad (EP1), no datos reales de personas:

* Sesgo de muestra: la cohorte histórica sobrerrepresenta urbanos, hombres y 25-45 años.
* Variables proxy: marca de teléfono, tipo de plan, antigüedad de línea y comuna de la
  antena dependen del nivel socioeconómico (NSE), que a su vez depende de los atributos
  protegidos.
* Exclusión digital inversa: los perfiles "thin file" tienen menos señal, NO peor pago.
* Sesgo de medición: los pagos en efectivo (corresponsales) se concilian con rezago, por lo
  que el atraso REGISTRADO y la mora REGISTRADA quedan inflados para quienes pagan así.

La variable objetivo real `incumplio` se genera SOLO a partir de la disciplina de pago y de
un shock de ingreso, ambos independientes de los atributos protegidos. Por construcción,
cualquier brecha de aprobación entre grupos es atribuible a los datos y al modelo.
"""
from __future__ import annotations

import hashlib
import string

import numpy as np
import pandas as pd

from common import PARAMS, ruta, rng, sigmoid, guardar_json

P = PARAMS["datos"]
MESES = P["meses_historial"]

PREFIJO_TEL = {"CL": "56", "PE": "51", "CO": "57", "MX": "52"}
MARCAS = {
    "alta": ["iPhone", "Galaxy S", "Pixel"],
    "media": ["Galaxy A", "Moto G", "Redmi Note"],
    "baja": ["Redmi", "Alcatel", "ZTE Blade", "Moto E"],
}
OPERADORES = {"CL": ["Movistar", "Entel", "WOM"], "PE": ["Movistar", "Claro", "Entel"],
              "CO": ["Claro", "Movistar", "Tigo"], "MX": ["Telcel", "AT&T", "Movistar"]}


# ---------------------------------------------------------------- identificadores
def _dv_rut(num: int) -> str:
    s, m = 0, 2
    for d in reversed(str(num)):
        s += int(d) * m
        m = 2 if m == 7 else m + 1
    r = 11 - s % 11
    return "0" if r == 11 else "K" if r == 10 else str(r)


def _id_nacional(pais: str, g: np.random.Generator) -> str:
    if pais == "CL":
        n = int(g.integers(8_000_000, 26_000_000))
        return f"{n}-{_dv_rut(n)}"
    if pais == "PE":
        return f"{int(g.integers(10_000_000, 79_999_999)):08d}"
    if pais == "CO":
        return str(int(g.integers(10_000_000, 1_299_999_999)))
    letras = string.ascii_uppercase
    return ("".join(g.choice(list(letras), 4)) + f"{int(g.integers(0, 999999)):06d}"
            + "".join(g.choice(list("HM"), 1)) + "".join(g.choice(list(letras), 5))
            + f"{int(g.integers(0, 99)):02d}")


def _telefono(pais: str, g: np.random.Generator) -> str:
    if pais == "CL":
        return "+569" + f"{int(g.integers(0, 99_999_999)):08d}"
    if pais == "PE":
        return "+519" + f"{int(g.integers(0, 99_999_999)):08d}"
    if pais == "CO":
        return "+573" + f"{int(g.integers(0, 999_999_999)):09d}"
    return "+52" + f"{int(g.integers(2_000_000_000, 9_999_999_999)):010d}"


def _formatear_rut(rut: str, g) -> str:
    num, dv = rut.split("-")
    estilo = g.integers(0, 3)
    if estilo == 0:
        return f"{int(num):,}".replace(",", ".") + "-" + dv
    if estilo == 1:
        return rut
    return num + dv.lower()


def _formatear_tel(tel: str, g) -> str:
    estilo = g.integers(0, 3)
    if estilo == 0:
        return tel
    if estilo == 1:
        return tel[1:]                      # sin "+"
    t = tel[1:]
    return f"+{t[:2]} {t[2:3]} {t[3:7]} {t[7:]}"


def _typo(s: str, g) -> str:
    i = int(g.integers(0, len(s)))
    c = s[i]
    if c.isdigit():
        return s[:i] + str((int(c) + 1) % 10) + s[i + 1:]
    return s[:i] + "X" + s[i + 1:]


# ---------------------------------------------------------------- población
def generar_poblacion(n: int, g: np.random.Generator, inicio: str, fin: str) -> pd.DataFrame:
    paises = list(P["paises"].keys())
    pais = g.choice(paises, n, p=list(P["paises"].values()))
    genero = g.choice(["F", "M"], n)
    edad = np.clip(np.round(g.normal(40, 14, n)), 18, 78).astype(int)
    p_rural = pd.Series(pais).map({"CL": 0.13, "PE": 0.24, "CO": 0.20, "MX": 0.21}).to_numpy()
    zona = np.where(g.random(n) < p_rural, "rural", "urbana")
    rural = (zona == "rural").astype(float)
    mujer = (genero == "F").astype(float)
    mayor60 = (edad >= 60).astype(float)
    p_inf = np.clip(0.40 + 0.18 * rural + 0.07 * mujer + 0.10 * mayor60, 0, 0.95)
    sector = np.where(g.random(n) < p_inf, "informal", "formal")
    informal = (sector == "informal").astype(float)

    # Nivel socioeconómico latente: depende de atributos protegidos (no entra al modelo)
    nse = g.normal(0, 1, n) + 0.7 * (1 - rural) - 0.6 * informal - 0.35 * mayor60 - 0.15 * mujer

    # Comportamiento real: independiente de atributos protegidos
    disciplina = g.normal(0, 1, n)
    shock = g.normal(0, 1, n)
    b0 = _calibrar_intercepto(disciplina, shock, P["tasa_incumplimiento_objetivo"])
    incumplio = (g.random(n) < sigmoid(b0 - 1.6 * disciplina + 0.6 * shock)).astype(int)

    # Canal de pago en efectivo (corresponsales): se concilia con rezago
    efectivo = g.random(n) < sigmoid(-0.9 - 1.1 * nse + 0.9 * rural + 0.4 * mayor60)
    # Mora registrada por el sistema histórico: pagos en efectivo no conciliados al corte
    falso_mora = efectivo & (incumplio == 0) & (g.random(n) < 0.20)
    incumplio_reg = np.where(falso_mora, 1, incumplio)

    # Perfil thin file: poca huella digital (no implica peor pago)
    thin = g.random(n) < sigmoid(-1.6 - 0.8 * nse + 1.4 * mayor60 + 0.7 * rural
                                  + 0.6 * mujer * informal)

    ts0, ts1 = pd.Timestamp(inicio).value, pd.Timestamp(fin).value
    fecha = pd.to_datetime(g.integers(ts0, ts1, n)).normalize()

    return pd.DataFrame({
        "pais": pais, "genero": genero, "edad": edad, "zona": zona, "sector_laboral": sector,
        "nse": nse, "disciplina": disciplina, "shock": shock, "paga_efectivo": efectivo,
        "thin_file": thin, "incumplio": incumplio, "incumplio_registrado": incumplio_reg,
        "fecha_solicitud": fecha,
    })


def _calibrar_intercepto(d, s, objetivo):
    lo, hi = -6.0, 2.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if sigmoid(mid - 1.6 * d + 0.6 * s).mean() > objetivo:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def muestrear_historico(pob: pd.DataFrame, n: int, g) -> pd.DataFrame:
    s = P["sesgo_muestra"]
    w = np.ones(len(pob))
    w *= np.where(pob.zona == "rural", s["rural"], s["urbana"])
    w *= np.where(pob.genero == "F", s["mujer"], s["hombre"])
    w *= np.where(pob.edad >= 60, s["edad_60_mas"],
                  np.where(pob.edad.between(25, 45), s["edad_25_45"], s["edad_otro"]))
    w *= np.where((pob.genero == "F") & (pob.sector_laboral == "informal"), s["mujer_informal"], 1)
    idx = g.choice(len(pob), n, replace=False, p=w / w.sum())
    return pob.iloc[np.sort(idx)].reset_index(drop=True)


# ---------------------------------------------------------------- fuentes
def construir_fuentes(sol: pd.DataFrame, g) -> dict[str, pd.DataFrame]:
    n = len(sol)
    nse, disc = sol.nse.to_numpy(), sol.disciplina.to_numpy()
    thin = sol.thin_file.to_numpy()
    rural = (sol.zona == "rural").to_numpy()

    def _unicos(fn):
        vistos, out = set(), []
        for p in sol.pais:
            v = fn(p, g)
            while v in vistos:
                v = fn(p, g)
            vistos.add(v)
            out.append(v)
        return out

    ids_nac = _unicos(_id_nacional)
    tels = _unicos(_telefono)
    emails = [f"cliente{i:06d}.{p.lower()}@correo.test" for i, p in zip(sol.solicitud_id, sol.pais)]

    # ---- 1. Telecomunicaciones: líneas (estático) + actividad mensual
    p_post = sigmoid(-0.6 + 1.3 * nse - 0.8 * thin)
    tipo_plan = np.where(g.random(n) < p_post, "postpago", "prepago")
    u = g.random(n)
    p_alta, p_baja = sigmoid(-1.4 + 1.4 * nse), sigmoid(-0.6 - 1.3 * nse)
    gama = np.where(u < p_alta, "alta", np.where(u > 1 - p_baja, "baja", "media"))
    marca = np.array([g.choice(MARCAS[x]) for x in gama])
    antig = np.where(thin, g.integers(1, 9, n),
                     np.clip(np.round(g.gamma(2.2, 18, n) + 8 * nse), 6, 240)).astype(int)
    # 40 comunas por país ordenadas por NSE; la antena refleja el NSE del barrio
    comuna_rank = np.clip(np.round(19.5 + 9 * nse + g.normal(0, 5, n) - 6 * rural), 0, 39).astype(int)
    comuna = [f"{p}-C{r:02d}" for p, r in zip(sol.pais, comuna_rank)]
    operador = [g.choice(OPERADORES[p]) for p in sol.pais]
    lineas = pd.DataFrame({
        "numero_movil": [_formatear_tel(t, g) for t in tels], "operador": operador,
        "tipo_plan": tipo_plan, "marca_telefono": marca, "gama_equipo": gama,
        "antiguedad_linea_meses": antig, "comuna_antena": comuna,
    })

    meses_tel = np.minimum(MESES, antig)
    rows = np.repeat(np.arange(n), meses_tel)
    mes_rel = np.concatenate([-np.arange(1, m + 1) for m in meses_tel])
    nse_r, disc_r, thin_r = nse[rows], disc[rows], thin[rows]
    n_rec = g.poisson(np.clip(2.5 + 0.6 * disc_r - 1.0 * thin_r, 0.3, None))
    monto_rec = np.round(np.exp(g.normal(2.3 + 0.35 * nse_r, 0.4)) * np.maximum(n_rec, 0), 2)
    post_r = tipo_plan[rows] == "postpago"
    atraso_post = np.where(post_r, np.maximum(0, np.round(g.normal(1.5 - 2.5 * disc_r, 2.5))), np.nan)
    telecom = pd.DataFrame({
        "numero_movil": np.array(lineas.numero_movil)[rows], "mes_rel": mes_rel,
        "n_recargas": n_rec, "monto_recargas": monto_rec,
        "datos_gb": np.round(np.clip(g.normal(6 + 2 * nse_r - 3 * thin_r, 2), 0.1, None), 2),
        "atraso_postpago_dias": atraso_post,
    })

    # ---- 2. Servicios básicos: electricidad, agua y gas (titular de la cuenta)
    meses_srv = np.where(thin, g.integers(0, 3, n), MESES)
    srv = []
    for tipo, p_tiene in (("electricidad", 0.95), ("agua", 0.85), ("gas", 0.55)):
        tiene = g.random(n) < p_tiene
        m = np.where(tiene, meses_srv, 0)
        r = np.repeat(np.arange(n), m)
        mr = np.concatenate([-np.arange(1, k + 1) for k in m]) if m.sum() else np.array([])
        real = np.maximum(0, np.round(g.normal(1.0 - 3.0 * disc[r], 2.5)))
        ef = sol.paga_efectivo.to_numpy()[r]
        # Pago en corresponsal: llega 1 a 3 días después a la empresa y a veces queda pendiente
        rezago_conc = np.where(ef, g.integers(1, 4, len(r)) + np.where(g.random(len(r)) < 0.30,
                                                                        g.integers(3, 9, len(r)), 0), 0)
        srv.append(pd.DataFrame({
            "rut_dni_titular": [ids_nac[i] for i in r], "tipo_servicio": tipo, "mes_rel": mr,
            "monto": np.round(np.exp(g.normal(3.3 + 0.3 * nse[r], 0.35)), 2),
            "dias_atraso_registrado": real + rezago_conc,
            "fecha_pago_efectiva_dias_atraso": real,   # disponible solo tras conciliación
            "canal_pago": np.where(ef, "corresponsal", "digital"),
        }))
    servicios = pd.concat(srv, ignore_index=True)
    # formatos heterogéneos de identificador + 1,5% de errores de digitación
    pais_srv = servicios.rut_dni_titular.map(dict(zip(ids_nac, sol.pais)))
    ids_fmt = [(_formatear_rut(x, g) if p == "CL" else x) for x, p in zip(servicios.rut_dni_titular, pais_srv)]
    err = g.random(len(ids_fmt)) < 0.015
    servicios["rut_dni_titular"] = [(_typo(x, g) if e else x) for x, e in zip(ids_fmt, err)]

    # ---- 3. Billeteras digitales y marketplaces
    presencia = np.where(thin, 0.15, sigmoid(1.0 + 0.8 * nse))
    activo = g.random(n) < presencia
    meses_mk = np.where(activo, np.where(thin, g.integers(1, 3, n), MESES), 0)
    r = np.repeat(np.arange(n), meses_mk)
    mr = np.concatenate([-np.arange(1, k + 1) for k in meses_mk])
    lam = np.exp(0.6 + 0.35 * disc[r] + 0.25 * nse[r])
    n_compras = g.poisson(lam)
    marketplace = pd.DataFrame({
        "email_sha256": [hashlib.sha256(emails[i].encode()).hexdigest() for i in r],
        "mes_rel": mr, "n_compras": n_compras,
        "ticket_promedio": np.round(np.exp(g.normal(3.0 + 0.35 * nse[r], 0.4)), 2),
        "n_reclamos": g.poisson(0.05 + 0.12 * np.clip(-disc[r], 0, None) * (n_compras > 0)),
        "n_devoluciones": g.poisson(0.08 + 0.10 * np.clip(-disc[r], 0, None) * (n_compras > 0)),
    })

    # ---- 4. Metadatos de la app de VFG (una fila por solicitud)
    so = np.where(np.isin(marca, ["iPhone"]), "iOS", "Android")
    app = pd.DataFrame({
        "solicitud_id": sol.solicitud_id,
        "tiempo_pantallas_seg": np.round(np.clip(g.normal(420 - 25 * disc, 90, n), 60, None)),
        "velocidad_formulario_seg": np.round(np.clip(g.normal(180 + 35 * (sol.edad.to_numpy() >= 60)
                                                              - 10 * disc, 45, n), 30, None)),
        "sistema_operativo": so, "dispositivo_gama": gama,
        "n_ediciones_formulario": g.poisson(np.clip(2 - 0.5 * disc, 0.2, None)),
    })

    # ---- 5. Redes sociales públicas (solo con opt-in; no se lee contenido)
    opt_in = g.random(n) < np.where(thin, 0.25, 0.6)
    redes = pd.DataFrame({
        "solicitud_id": sol.solicitud_id[opt_in].to_numpy(),
        "antiguedad_cuenta_meses": np.round(np.clip(g.normal(70 - 40 * thin, 30, n), 1, None))[opt_in],
        "tamano_red": np.round(np.exp(g.normal(5.2 + 0.4 * nse - 1.2 * thin, 0.6)))[opt_in],
    })

    # ---- 6. Biometría de onboarding (uso exclusivo antifraude, no entra al modelo)
    manual = (sol.sector_laboral == "informal").to_numpy()
    p_fallo = 0.03 + 0.09 * (sol.edad.to_numpy() >= 60) + 0.05 * manual
    biometria = pd.DataFrame({
        "solicitud_id": sol.solicitud_id,
        "match_score": np.round(np.clip(g.normal(0.93 - 0.08 * (sol.edad.to_numpy() >= 60), 0.05), 0, 1), 3),
        "fallo_primer_intento": (g.random(n) < p_fallo).astype(int),
    })

    # ---- marca de tiempo y rezago de disponibilidad (fuentes 1, 2 y 3)
    rez = P["rezago_horas"]
    for df, (lo, hi) in ((telecom, rez["telecom"]), (servicios, rez["servicios"]),
                         (marketplace, rez["marketplace"])):
        # día del evento dentro del mes relativo (0 = día de la solicitud hacia atrás)
        df["dias_antes_solicitud"] = (-df["mes_rel"] - 1) * 30 + g.integers(0, 30, len(df))
        df["rezago_horas"] = g.integers(lo, hi + 1, len(df))

    solicitudes = pd.DataFrame({
        "solicitud_id": sol.solicitud_id, "pais": sol.pais, "fecha_solicitud": sol.fecha_solicitud,
        "id_nacional": ids_nac, "telefono": tels,
        "email": [e.upper() if g.random() < 0.3 else f" {e} " for e in emails],
        "monto_solicitado_usd": np.round(np.exp(g.normal(np.log(320), 0.45, n)), 0),
        "plazo_meses": g.choice([3, 4, 5, 6, 8], n, p=[0.15, 0.2, 0.35, 0.2, 0.1]),
        "cohorte": sol.cohorte,
    })
    return {"solicitudes": solicitudes, "telecom_lineas": lineas, "telecom_actividad": telecom,
            "servicios": servicios, "marketplace": marketplace, "app_metadatos": app,
            "redes_optin": redes, "biometria": biometria}


def main() -> None:
    g = rng()
    pob = generar_poblacion(P["n_poblacion"], g, "2025-01-01", "2025-09-30")
    hist = muestrear_historico(pob, P["n_historico"], g)
    hist["cohorte"] = "historica"
    rec = generar_poblacion(P["n_reciente"], g, "2025-10-01", "2025-12-31")
    rec["cohorte"] = "reciente"
    sol = pd.concat([hist, rec], ignore_index=True).sort_values("fecha_solicitud").reset_index(drop=True)
    sol.insert(0, "solicitud_id", np.arange(1, len(sol) + 1))
    sol["tramo_edad"] = pd.cut(sol.edad, [17, 24, 45, 59, 120], labels=["18-24", "25-45", "46-59", "60+"]).astype(str)

    fuentes = construir_fuentes(sol, g)
    raw = ruta("raw")
    for nombre, df in fuentes.items():
        df.to_parquet(raw / f"{nombre}.parquet", index=False)

    # Atributos protegidos y etiquetas: tablas separadas, NUNCA entran al modelo
    sol[["solicitud_id", "genero", "edad", "tramo_edad", "zona", "sector_laboral"]].to_parquet(
        raw / "atributos_protegidos.parquet", index=False)
    sol[["solicitud_id", "incumplio", "incumplio_registrado"]].to_parquet(raw / "resultados.parquet", index=False)
    # Variables latentes, solo para validar el generador (no las usa el pipeline)
    sol[["solicitud_id", "nse", "disciplina", "thin_file", "paga_efectivo"]].to_parquet(
        raw / "_latentes_generador.parquet", index=False)

    resumen = {
        "n_solicitudes": len(sol),
        "por_cohorte": sol.cohorte.value_counts().to_dict(),
        "filas_por_fuente": {k: len(v) for k, v in fuentes.items()},
        "tasa_incumplio_real": round(float(sol.incumplio.mean()), 4),
        "tasa_incumplio_registrado": round(float(sol.incumplio_registrado.mean()), 4),
        "composicion": {
            c: {coh: sol[sol.cohorte == coh][c].value_counts(normalize=True).round(3).to_dict()
                for coh in ("historica", "reciente")}
            for c in ("zona", "genero", "tramo_edad", "sector_laboral", "pais")
        },
        "incumplio_real_por_grupo": {
            c: sol.groupby(c).incumplio.mean().round(4).to_dict()
            for c in ("zona", "genero", "tramo_edad", "sector_laboral")
        },
        "incumplio_registrado_por_grupo": {
            c: sol.groupby(c).incumplio_registrado.mean().round(4).to_dict()
            for c in ("zona", "genero", "tramo_edad", "sector_laboral")
        },
    }
    guardar_json(resumen, ruta("reportes") / "resumen_generador.json")
    print(f"Generadas {len(sol):,} solicitudes sintéticas")
    print(f"Incumplimiento real {resumen['tasa_incumplio_real']:.2%} · registrado {resumen['tasa_incumplio_registrado']:.2%}")


if __name__ == "__main__":
    main()
