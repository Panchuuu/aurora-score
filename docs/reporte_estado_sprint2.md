# Reporte de estado · Sprint 2 (F3 Modelado)

**Proyecto:** AURORA SCORE · Vertex Financial Group · **Período:** 17-11 al 28-11-2026 · **Corte del plan:** M4–M8
**Preparado por:** Francisco Gaete, Oscar Oreste (consultores externos) · **Estado general:** 🟢 Verde en
calidad y 🟡 amarillo en esfuerzo (+20,0 %)

> Prototipo con datos sintéticos que reproducen la estructura y los sesgos del caso.

## 1. Avance
| Paquete WBS | Tarjetas | Hechas | Avance del corte |
|---|---:|---:|---:|
| 1.0 Gestión del proyecto | 1 | 1 | 100 % |
| 2.0 Gobernanza y cumplimiento | 1 | 1 | 100 % |
| 4.0 Modelo analítico | 8 | 7 | 88 % (AUR-24 replanificada a S3) |
| 5.0 Motor de decisión y agentes | 2 | 2 | 100 % |
| 6.0 Despliegue y expansión | 3 | 3 | 100 % |
| **Total Sprint 2** | **14 + 1 en backlog** | **14** | 50 h estimadas, 60 h reales |

## 2. Resultados (cohorte de prueba de octubre a diciembre de 2025, 12.000 solicitudes)
| Indicador | v1-base | v2-mitigado | Criterio |
|---|---:|---:|---|
| AUC (mora real) | 0,745 | **0,808** | — |
| KS | 0,333 | **0,478** | — |
| Brecha máxima de aprobación | 22,3 pp (zona) | **1,49 pp** | ≤ 5 pp |
| Disparate impact mínimo | 0,54 | **0,98** | ≥ 0,80 |
| Tasa de aprobación | 44,4 % | 74,8 % | — |
| Mora de aprobados | 4,2 % | 5,2 % | — |
| Latencia p95 de la ruta de decisión | — | **1.816 ms** | < 8.000 ms |
| Rechazos con 3 a 5 factores explicados | — | **100 %** (3.029) | RF-05 |
| Integridad del registro de auditoría | — | 12.000 registros; detecta manipulación en la línea 500 | RF-12 |

## 3. Hitos
- **H3 · Modelo validado y auditado (M8):** el criterio de equidad ya se cumple, pero el hito queda **pendiente**
  hasta cerrar el *reject inference* (AUR-24) y validar la mora con 12 meses de comportamiento observado
  (condición 3 del directorio).

## 4. Desviaciones del sprint
- **D3:** el modelo base no cumple el criterio de equidad. Corregida con v2.
- **D4:** sobreajuste del primer entrenamiento. Corregido con *early stopping* temporal.
- **D5:** sesgo de medición no previsto; se agregó AUR-22 por control de cambios (+4 h).
- **D6:** herramienta de PDF no disponible (+1 h).
- **D7:** *reject inference* replanificado al Sprint 3.

## 5. Riesgos de la matriz RP
| Riesgo | Situación |
|---|---|
| RP-07 Criterio de equidad | **Materializado y controlado.** Se consumió una de las dos iteraciones de reserva. |
| RP-05 Crecimiento del alcance | **Controlado.** AUR-22 entró por control de cambios dentro del paquete 4.3. |
| RP-06 Umbral de 8 segundos | **No materializado.** p95 de 1.816 ms con supuestos de red pesimistas; holgura de 6,2 s. |
| RP-04 Base del piloto | Mitigado con reponderación a la población objetivo. |
| RP-08 Dependencia del proveedor | Mitigado: código, notebooks y documentación en un repositorio del equipo. |

## 6. Decisiones tomadas
1. Promover **v2-mitigado** como candidato. El v1-base queda registrado solo como línea de comparación.
2. Usar TreeSHAP nativo de LightGBM (`pred_contrib`) en vez de la librería `shap`: el cálculo es el mismo y se
   elimina una dependencia.
3. Monitorear la equidad aparte del drift, porque el PSI no detectó el sesgo de muestra.
4. Priorizar la conciliación (AUR-22) por sobre el *reject inference* (AUR-24), por su impacto medido.

## 7. Próximo sprint (S3)
*Reject inference* (AUR-24), pruebas de carga a tres veces el volumen y preparación del expediente de
auditoría de sesgo para la firma de Cumplimiento.
