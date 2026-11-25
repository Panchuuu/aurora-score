# Planificado vs. ejecutado — Sprint 1 y Sprint 2

Corte del plan de 14 meses (EP3) que se ejecuta en este prototipo: fase **F2** (M2–M5) y comienzo de **F3** (M4–M8), en dos iteraciones de dos semanas, tal como define el plan. Datos sintéticos.

Fuente única: `docs/tareas.csv`. Este documento se regenera con `python src/gestion.py`.

## Resumen por sprint

| Sprint | Tarjetas | Hechas | Est. (h) | Real (h) | Desviación de esfuerzo |
|---|---:|---:|---:|---:|---:|
| S1 | 9 | 9 | 38 | 44 | +15,8 % |
| S2 | 14 | 14 | 50 | 60 | +20,0 % |

## Avance por paquete de la WBS (sobre las tarjetas de este corte)

| Paquete WBS | Tarjetas del corte | Hechas | Avance del corte |
|---|---:|---:|---:|
| 1.0 Gestión del proyecto | 3 | 3 | 100 % |
| 2.0 Gobernanza y cumplimiento | 2 | 2 | 100 % |
| 3.0 Plataforma de datos | 5 | 5 | 100 % |
| 4.0 Modelo analítico | 9 | 8 | 89 % |
| 5.0 Motor de decisión y agentes | 2 | 2 | 100 % |
| 6.0 Despliegue y expansión | 3 | 3 | 100 % |

## Detalle por tarjeta

| Tarjeta | Tarea | WBS | Resp. | Est. (h) | Real (h) | Estado | Desviación |
|---|---|---|---|---:|---:|---|---|
| AUR-01 | Repositorio y parámetros del prototipo | 1.2 | Francisco | 3 | 3 | Hecho | — |
| AUR-02 | Generador sintético de las seis fuentes | 3.3 | Oscar | 8 | 11 | Hecho | +3 h (+38 %) D1 |
| AUR-03 | Ingesta con rezago de 24 a 72 h | 3.2 | Francisco | 5 | 5 | Hecho | — |
| AUR-04 | Resolución de identidad por país | 3.5 | Oscar | 5 | 6 | Hecho | +1 h (+20 %) D2 |
| AUR-05 | Auditoría de representatividad de la muestra | 2.4 | Francisco | 3 | 3 | Hecho | — |
| AUR-06 | Feature store precalculado | 3.6 | Oscar | 6 | 8 | Hecho | +2 h (+33 %) D1 |
| AUR-07 | Notebook 01 · exploración de datos | 3.5 | Francisco | 3 | 3 | Hecho | — |
| AUR-08 | Notebook 02 · ingeniería de variables | 4.1 | Oscar | 3 | 3 | Hecho | — |
| AUR-09 | Reporte de estado Sprint 1 | 1.2 | Francisco | 2 | 2 | Hecho | — |
| AUR-10 | Modelo base LightGBM con split temporal | 4.2 | Francisco | 5 | 7 | Hecho | +2 h (+40 %) D4 |
| AUR-11 | Versionado de modelos con hash | 4.2 | Oscar | 2 | 2 | Hecho | — |
| AUR-12 | Motor de decisión con umbrales por país | 5.2 | Oscar | 3 | 3 | Hecho | — |
| AUR-13 | Explicabilidad TreeSHAP en lenguaje natural | 4.4 | Francisco | 5 | 6 | Hecho | +1 h (+20 %) |
| AUR-14 | Auditoría de equidad | 2.4 | Oscar | 4 | 4 | Hecho | — |
| AUR-15 | Mitigación de sesgo y modelo v2 | 4.3 | Francisco | 6 | 8 | Hecho | +2 h (+33 %) D3 |
| AUR-16 | Benchmark de latencia contra 8 s | 6.1 | Oscar | 3 | 3 | Hecho | — |
| AUR-17 | Monitoreo de drift PSI y KS | 6.2 | Oscar | 3 | 3 | Hecho | — |
| AUR-18 | Registro de auditoría inmutable | 5.5 | Francisco | 3 | 3 | Hecho | — |
| AUR-19 | Dashboard de monitoreo en Streamlit | 6.2 | Oscar | 6 | 6 | Hecho | — |
| AUR-20 | Notebooks 03 a 05 | 4.2 | Francisco | 4 | 4 | Hecho | — |
| AUR-21 | Reporte de estado Sprint 2 e informe EP5 | 1.2 | Francisco | 4 | 5 | Hecho | +1 h (+25 %) D6 |
| AUR-22 | Conciliación de atraso y mora con fecha efectiva | 4.3 | Francisco | 0 | 4 | Hecho | +4 h (no planificada) D5 |
| AUR-23 | Model card del modelo v2 | 4.5 | Oscar | 2 | 2 | Hecho | — |
| AUR-24 | Reject inference | 4.3 | Francisco | 5 | 0 | Backlog | replanificada a S3 D7 |

Las horas reales son las registradas por el equipo en cada tarjeta al cerrarla.