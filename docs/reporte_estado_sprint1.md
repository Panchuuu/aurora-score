# Reporte de estado · Sprint 1 (F2 Adquisición y comprensión de datos)

**Proyecto:** AURORA SCORE · Vertex Financial Group · **Período:** 03-11 al 14-11-2026 · **Corte del plan:** M2–M5
**Preparado por:** Francisco Gaete, Oscar Oreste (consultores externos) · **Estado general:** 🟡 Amarillo
(alcance cumplido con +15,8 % de esfuerzo)

> Prototipo con datos sintéticos que reproducen la estructura y los sesgos del caso.

## 1. Avance
| Paquete WBS | Tarjetas | Hechas | Avance del corte |
|---|---:|---:|---:|
| 1.0 Gestión del proyecto | 2 | 2 | 100 % |
| 2.0 Gobernanza y cumplimiento | 1 | 1 | 100 % |
| 3.0 Plataforma de datos | 5 | 5 | 100 % |
| 4.0 Modelo analítico | 1 | 1 | 100 % |
| **Total Sprint 1** | **9** | **9** | **100 %** · 38 h estimadas, 44 h reales |

## 2. Entregables del sprint
- Generador sintético de las seis fuentes: 42.000 solicitudes en CL, PE, CO y MX, con más de un millón de
  registros entre fuentes.
- Ingesta con rezago de 24 a 72 h: entre 0,9 % y 1,3 % de los eventos aún no está disponible al momento de
  decidir, y queda marcado.
- Resolución de identidad por país: 98,5 % de enlace en servicios básicos y 100 % en las demás fuentes.
- Feature store con 48 variables por solicitud.
- Notebooks 01 y 02.

## 3. Hitos
- **H2 · Plataforma de datos operativa (M5):** alcanzado **a escala de prototipo**. Las seis fuentes se
  ingieren, se enlazan y alimentan el feature store de forma reproducible.

## 4. Desviaciones del sprint
- **D1:** llaves duplicadas en el generador (+5 h). Corregida, con un control automático de unicidad.
- **D2:** identificadores ambiguos en servicios básicos (+1 h). Corregida.

## 5. Riesgos de la matriz RP
| Riesgo | Situación |
|---|---|
| RP-04 Base del piloto insuficiente | **Materializado parcialmente.** La auditoría de representatividad (AUR-05) muestra que la base histórica tiene 9,7 % de población rural frente a 18,2 % en la objetivo, y 4,0 % de mayores de 60 frente a 8,1 %. Se detectó en el Sprint 1, antes de modelar, tal como pedía la respuesta del plan. |
| RP-07 Criterio de equidad | En vigilancia: el hallazgo de RP-04 y el de mora registrada vs. real anticipan que el modelo base no cumplirá. |
| RP-05 Crecimiento del alcance | En vigilancia: el hallazgo de medición puede requerir una tarjeta nueva. |

## 6. Decisiones tomadas
1. Separar los atributos protegidos y las etiquetas en tablas que **nunca** entran al modelo y se usan solo
   para auditar.
2. Usar split temporal (enero a septiembre para entrenar, octubre a diciembre para evaluar) en vez de uno
   aleatorio.
3. Llevar al Sprint 2 la evidencia de que la mora registrada (16,4 %) no coincide con la real (10,9 %).

## 7. Próximo sprint
Modelo base, auditoría de equidad, mitigación, explicabilidad, latencia, monitoreo, registro de auditoría y
panel.
