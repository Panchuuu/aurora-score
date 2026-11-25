# AURORA SCORE · Prototipo de scoring alternativo con control de sesgo

**SCY1102 Gestión de Proyectos de Datos · Duoc UC · Sección 001V · 2026**
Francisco Gaete · Oscar Oreste — Docente: Jose Luis Barria Vásquez

> ⚠️ **Caso ficticio y datos 100 % sintéticos.** Vertex Financial Group (VFG) y AURORA SCORE son un caso
> académico. Ningún dato de este repositorio corresponde a personas reales.

Este repositorio implementa el corte del plan de proyecto (EP3) que va del **mes 2 al mes 5**: el **Sprint 1**
(fase F2, adquisición y comprensión de datos) y el **Sprint 2** (fase F3, modelado). Cubre ingesta multifuente
con rezago, resolución de identidad, feature store, modelo de gradient boosting, explicabilidad, auditoría de
equidad con mitigación, benchmark de latencia, monitoreo y registro de auditoría inmutable.

## Resultados principales (cohorte de prueba de octubre a diciembre de 2025, 12.000 solicitudes)

| Indicador | v1-base | v2-mitigado | Criterio del plan |
|---|---:|---:|---|
| AUC (mora real) | 0,745 | **0,808** | — |
| Brecha máxima de aprobación entre grupos | 22,3 pp | **1,49 pp** | ≤ 5 pp |
| Disparate impact mínimo | 0,54 | **0,98** | ≥ 0,80 |
| Latencia p95 de la decisión | — | **1.816 ms** | < 8.000 ms (RNF-01) |
| Rechazos explicados con 3 a 5 factores | — | **100 %** | RF-05 |

El modelo base **no cumple** el criterio de equidad: aprueba al 26 % de los solicitantes rurales y al 48 % de
los urbanos, con la misma mora real. Tres medidas de mitigación lo corrigen sin perder capacidad predictiva:
conciliación de la mora registrada, eliminación de proxies y reponderación con variables de cobertura
(ver `reports/ablacion_mitigacion.csv`).

## Cómo reproducir todo

Requiere Python 3.11.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt

python src/pipeline.py            # datos sintéticos → ingesta → features → modelos → equidad → latencia → auditoría → figuras (~80 s)
python src/gestion.py             # regenera tarjetas, planificado vs. ejecutado y model card
jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
streamlit run dashboard/app.py    # panel de monitoreo en http://localhost:8501
```

La semilla está fijada en `config/params.yaml` (`semilla: 2026`), por lo que cada ejecución produce los mismos
datos y las mismas métricas.

## Estructura

```
config/params.yaml      umbrales por país, semilla, rutas y criterios de equidad
src/
  generate_data.py      generador sintético de las seis fuentes con los sesgos del EP1      AUR-02
  ingest.py             ingesta y consolidación con rezago de 24-72 h                         AUR-03  RF-01
  identity.py           resolución de identidad por país                                     AUR-04  RF-02
  features.py           feature store precalculado (48 variables)                            AUR-06  RF-01 RNF-01
  train.py              LightGBM v1/v2, split temporal, versionado, ablación                 AUR-10/11/15  RF-03
  decision.py           motor de decisión con umbrales por país                              AUR-12  RF-04
  explain.py            TreeSHAP y factores de rechazo en lenguaje natural                   AUR-13  RF-05
  fairness.py           auditoría de equidad (5 pp, regla del 80 %) y detección de proxies   AUR-14  RF-11
  latency.py            benchmark de la ruta crítica contra 8 s                              AUR-16  RNF-01
  monitor.py            PSI y KS por variable y del score                                    AUR-17  RF-11
  audit_log.py          registro inmutable encadenado con SHA-256                            AUR-18  RF-12
  gestion.py            documentos de gestión desde docs/tareas.csv
  pipeline.py           ejecuta todo en orden
notebooks/              01 exploración · 02 features · 03 modelo · 04 equidad · 05 latencia
dashboard/app.py        Streamlit: desempeño, drift, equidad con semáforo, inclusión          AUR-19
models/                 modelos y registro con hash
reports/                métricas, tablas y figuras
docs/                   tareas, tarjetas Trello, plan vs. ejecución, reportes de estado, desviaciones, model card
```

## Gestión

- Tablero: Trello. El contenido de cada tarjeta está en [`docs/tarjetas_trello.md`](docs/tarjetas_trello.md).
- Planificado vs. ejecutado: [`docs/plan_vs_ejecucion.md`](docs/plan_vs_ejecucion.md).
- Reportes de estado: [Sprint 1](docs/reporte_estado_sprint1.md) · [Sprint 2](docs/reporte_estado_sprint2.md).
- Desviaciones y acciones correctivas: [`docs/desviaciones.md`](docs/desviaciones.md).
- Los commits citan el paquete de la WBS y la tarjeta: `feat(3.6): feature store precalculado — AUR-06`.

## Qué se simula y qué no

- Los datos son sintéticos. Por construcción, la mora real no depende de los atributos protegidos, así que
  cualquier brecha entre grupos se puede atribuir a los datos y al modelo.
- En el benchmark de latencia, el cómputo se mide de verdad. La red, la E/S del feature store y las llamadas a
  terceros se simulan con distribuciones pesimistas, y así se declara en `src/latency.py`.
- El prototipo implementa 48 de las más de 240 variables del caso: un subconjunto representativo de las seis
  fuentes.
