# Model card · AURORA SCORE v2-mitigado

> Modelo entrenado con **datos sintéticos**. Caso ficticio con fines académicos (SCY1102, Duoc UC).

| Campo | Valor |
|---|---|
| Versión | v2-mitigado |
| Algoritmo | LightGBM (gradient boosting) |
| SHA-256 | `3d3fe1b192eeb225bd78714b1ad85693d2f982250197852c1a273c13fb74533b` |
| Fecha de entrenamiento | 2026-11-25T14:18:12 |
| Variables | 43 (subconjunto representativo de las más de 240 del caso) |
| Split | temporal: entrena 2025-01-01 a 2025-09-29 (30,000 solicitudes), evalúa 2025-10-01 a 2025-12-30 (12,000) |
| Etiqueta | `incumplio` conciliado con la fecha efectiva de pago |
| Umbrales por país | {'CL': 0.13, 'PE': 0.13, 'CO': 0.12, 'MX': 0.12} |

## Uso previsto
Estimar la probabilidad de incumplimiento de solicitantes sin historial en burós, para créditos de consumo
digital de VFG en Chile y Perú durante el piloto ampliado. **No** está validado para Colombia ni México hasta
cumplir el hito de decisión de M11, ni para otros productos de crédito.

## Desempeño (cohorte reciente, mora real)
| Métrica | Valor |
|---|---|
| AUC-ROC | 0.8085 |
| KS | 0.4782 |
| AUC en entrenamiento | 0.8378 |
| Tasa de aprobación | 74.8% |
| Mora de aprobados | 5.24% |
| Mora de rechazados | 28.46% |

## Equidad (criterio del plan: brecha ≤ 5 pp y regla del 80 %)
| Atributo | Grupo con menor aprobación | Grupo con mayor aprobación | Brecha (pp) | Disparate impact |
|---|---|---|---:|---:|
| genero | M 74.4% | F 75.1% | 0.63 | 0.992 |
| zona | urbana 74.6% | rural 75.3% | 0.71 | 0.991 |
| tramo_edad | 46-59 73.7% | 18-24 75.2% | 1.49 | 0.980 |
| sector_laboral | informal 74.7% | formal 74.8% | 0.17 | 0.998 |

Veredicto: **cumple**. Los atributos protegidos no son variables del modelo.

## Medidas de mitigación aplicadas
1. Conciliación de atraso y mora con la fecha efectiva de pago (sesgo de medición).
2. Eliminación de variables con correlación > 0,35 con un atributo protegido: comuna_antena.
3. Reponderación de la cohorte histórica a la composición de la población objetivo y variables de cobertura de datos.

## Limitaciones conocidas
- Datos sintéticos: las cifras demuestran el mecanismo, no el desempeño esperado con datos reales.
- No incluye *reject inference*: el sesgo de retroalimentación (solo se observa el pago de los aprobados) queda pendiente (AUR-24).
- La validación del supuesto de mora exige 12 meses de comportamiento observado (condición 3 del directorio).
- Cada rechazo se explica con 3 a 5 factores TreeSHAP; la carta final requiere revisión legal por país.
