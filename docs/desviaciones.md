# Registro de desviaciones y acciones correctivas

Desviaciones **reales** ocurridas durante el Sprint 1 y el Sprint 2. Cada una indica qué se planificó, qué
ocurrió, la causa, el impacto, la acción correctiva y su estado. Las cifras salen de ejecutar el código
(`reports/`). Datos sintéticos.

| Id | Sprint | Tarjeta | Desviación | Impacto | Estado |
|---|---|---|---|---|---|
| D1 | S1 | AUR-02, AUR-06 | Llaves duplicadas en el generador: el feature store salió con 42.003 filas en vez de 42.000 | +5 h | Cerrada |
| D2 | S1 | AUR-04 | Identificadores ambiguos en la fuente de servicios básicos | +1 h | Cerrada |
| D3 | S2 | AUR-14, AUR-15 | El modelo base **no cumple** el criterio de equidad: brecha de 22,3 pp por zona | +2 h | Cerrada con v2 |
| D4 | S2 | AUR-10 | Sobreajuste del primer modelo: AUC 0,93 en entrenamiento vs. 0,74 en prueba | +2 h | Cerrada |
| D5 | S2 | AUR-22 | Sesgo de medición no previsto en el backlog: la mora registrada (16,4 %) no es la real (10,9 %) | +4 h no planificadas | Cerrada |
| D6 | S2 | AUR-21 | La herramienta prevista para generar el PDF (wkhtmltopdf) no estaba disponible | +1 h | Cerrada |
| D7 | S2 | AUR-24 | *Reject inference* planificado en F3 no se ejecutó en el Sprint 2 | Replanificada a S3 | Abierta |
| D8 | S2 | AUR-11 | Al clonar el repositorio, el hash del modelo no coincidía con el registrado | +1 h | Cerrada |

---

## D1 · Llaves duplicadas en el generador sintético
- **Planificado:** un feature store con una fila por solicitud (42.000).
- **Ocurrido:** la primera ejecución produjo 42.003 filas.
- **Causa:** el generador asignaba números móviles al azar sin controlar unicidad. Tres números se repitieron,
  la resolución de identidad enlazó dos líneas con la misma solicitud y el *join* duplicó filas.
- **Impacto:** +3 h en AUR-02 y +2 h en AUR-06. Sin el control, el entrenamiento habría contado dos veces a
  esas personas.
- **Acción correctiva:** unicidad garantizada de identificadores en el generador y un control preventivo:
  `features.py` ahora falla si una solicitud aparece dos veces (`assert solicitud_id.is_unique`).
- **Aprendizaje:** el control de calidad se escribe como prueba automática, no como revisión visual.

## D2 · Identificadores ambiguos en servicios básicos
- **Planificado:** normalizar el identificador con la regla de cada país.
- **Ocurrido:** la fuente de servicios no informa el país. Un RUT escrito sin guion (`123456789`) no se distingue
  de una cédula colombiana de 9 dígitos, y parte de los DNI peruanos de 8 dígitos pasan la validación del RUT.
- **Acción correctiva:** se generan ambas lecturas candidatas y se usa la que existe en el padrón de solicitudes.
  Tasa de enlace final: **98,5 %**. El 1,5 % restante corresponde a los errores de digitación inyectados a
  propósito. Esos registros se informan en `reports/calidad_identidad.csv`; no se descartan en silencio.
- **Recomendación para producción:** exigir a los proveedores el país dentro de la llave (cláusula en los
  contratos de datos, que conecta con RP-01).

## D3 · El modelo base no cumple el criterio de equidad (RP-07 materializado)
- **Planificado:** hito H3 con brecha de aprobación ≤ 5 pp entre grupos y regla del 80 %.
- **Ocurrido:** el modelo v1-base aprueba al 26,1 % de los solicitantes rurales y al 48,4 % de los urbanos
  (**brecha de 22,3 pp, disparate impact 0,54**), aunque la mora real de ambos grupos es la misma (11,0 % y
  11,1 %).
  Para descartar que la brecha se deba al umbral, se repitió la comparación al mismo volumen de aprobación que
  v2. Aun así quedó en **13,5 pp**.
- **Causa:** tres de los siete focos de sesgo documentados en el EP1 actúan juntos: el de medición, el de
  variables proxy y el de muestra.
- **Acción correctiva:** AUR-15 y AUR-22, que generan el modelo v2-mitigado. Resultado: **brecha máxima de
  1,49 pp** y disparate impact mínimo de 0,98. Cumple.
- **Gestión:** se consumió una de las dos iteraciones de reserva que el plan dejó para RP-07. Es exactamente la
  respuesta que el plan definió: medir la equidad desde la primera iteración.

## D4 · Sobreajuste del primer entrenamiento
- **Ocurrido:** el primer v1-base, con 400 árboles fijos, tuvo AUC de 0,93 en entrenamiento y de 0,74 en prueba.
- **Acción correctiva:** *early stopping* con validación temporal: el último mes del período de entrenamiento
  fija el número de árboles. Resultado: v2 con AUC de 0,84 en entrenamiento y 0,81 en prueba.

## D5 · Sesgo de medición no previsto en el backlog (control de cambios)
- **Planificado:** el EP3 asignaba a F3 la reponderación y el *reject inference* como medidas de mitigación.
- **Ocurrido:** la exploración del Sprint 1 mostró que la mora **registrada** (16,4 %) supera a la **real**
  (10,9 %) y que la diferencia se concentra en zonas rurales (21,5 % vs. 11,2 %). La causa son los pagos en
  corresponsales, que se concilian con rezago. Es el foco de medición del EP1.
- **Acción correctiva:** se creó la tarjeta AUR-22 por control de cambios. El cambio queda dentro del
  paquete 4.3 Mitigación de sesgo, por lo que no amplía el alcance del proyecto (RP-05). Consiste en conciliar
  el atraso y la mora con la fecha efectiva de pago.
- **Resultado:** en la ablación, esta medida por sí sola baja la brecha de 13,5 a 1,3 pp y sube el AUC de
  0,745 a 0,803. Es la medida de mayor efecto.

## D6 · Herramienta de generación de documentos
- **Ocurrido:** la versión de wkhtmltopdf prevista para generar el informe no estaba instalada en el equipo de
  trabajo.
- **Acción correctiva:** se generó el PDF desde HTML con el navegador Microsoft Edge en modo *headless* y se
  numeraron las páginas con `pypdf` + `reportlab`. El formato del informe no cambió.

## D7 · *Reject inference* replanificado al Sprint 3
- **Planificado:** *reject inference* dentro de F3 (EP3, lámina de fases).
- **Ocurrido:** no se ejecutó en el Sprint 2. Se priorizó AUR-22 porque el sesgo de medición tenía un impacto
  medido mayor y bloqueaba el criterio de equidad.
- **Impacto:** el sesgo de retroalimentación (solo se observa el pago de los aprobados) sigue abierto. No afecta
  a H2. Afecta a H3, previsto para M8, que tiene holgura.
- **Acción:** la tarjeta AUR-24 pasa al Sprint 3 con 5 h estimadas. Queda declarada como limitación en la
  model card.

## D8 · El hash del modelo no coincidía en un clon limpio
- **Planificado:** que el motor de decisión verifique el SHA-256 del modelo antes de cargarlo (RNF-09).
- **Ocurrido:** al clonar el repositorio publicado, el archivo del modelo v2 tenía otro hash
  (`aec9…` en vez de `3d3f…`). Por diseño, el motor se negó a cargarlo.
- **Causa:** LightGBM escribe en Windows una línea con fin `\r\n` dentro de un archivo con fines `\n`, y git
  normalizó ese fin de línea al guardarlo. El control funcionó: detectó un modelo alterado, aunque la
  alteración fuera involuntaria.
- **Acción correctiva:** `.gitattributes` marca `models/**` como binario y los modelos se volvieron a guardar
  byte a byte. Se verificó en un clon nuevo que ambos hashes coinciden con el registro.

---

### Hallazgo que no es desviación: el drift no detecta el sesgo de muestra
El PSI de las 43 variables del modelo quedó en estado **estable** (máximo 0,021), aunque la cohorte histórica
tiene la mitad de población rural que la objetivo (9,7 % vs. 18,2 %). Decisión: la equidad se monitorea con
métricas propias en el panel, y no se deduce de la ausencia de drift.
