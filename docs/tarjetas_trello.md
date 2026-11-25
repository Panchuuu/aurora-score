# Tablero Trello · AURORA SCORE — contenido de las tarjetas

Columnas del tablero: **Backlog · Planificado Sprint · En curso · En revisión · Hecho**.

Etiquetas sugeridas: `S1`, `S2`, `S3`, `WBS 1.x` a `WBS 6.x`, `Agregada` (control de cambios), `Desviación`.

Cada tarjeta traza a un paquete de la WBS del EP3 y a un requerimiento (RF/RNF). Los commits del repositorio citan el id de la tarjeta (por ejemplo `AUR-14`).


## Sprint 1 · F2 Adquisición y comprensión de datos (03-11 al 14-11-2026)

### AUR-01 · Repositorio y parámetros del prototipo

- **Columna:** Hecho
- **Descripción:** Estructura del repositorio, requirements con versiones, .gitignore y config/params.yaml con semilla, umbrales y criterios de equidad.
- **Paquete WBS:** 1.2 Seguimiento y control
- **Requerimiento:** RNF-09
- **Responsable:** Francisco Gaete
- **Estimación:** 3 h · **Real:** 3 h
- **Etiquetas:** S1, WBS 1.2
- **Evidencia:** `config/params.yaml`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-02 · Generador sintético de las seis fuentes

- **Columna:** Hecho
- **Descripción:** Genera 42.000 solicitudes en CL, PE, CO y MX con los sesgos del EP1 incorporados: muestra, proxies, exclusión digital inversa y medición. Semilla fija.
- **Paquete WBS:** 3.3 Conectores
- **Requerimiento:** RF-01
- **Responsable:** Oscar Oreste
- **Estimación:** 8 h · **Real:** 11 h
- **Etiquetas:** S1, WBS 3.3, Desviación
- **Desviación:** D1 (ver docs/desviaciones.md)
- **Evidencia:** `src/generate_data.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-03 · Ingesta con rezago de 24 a 72 h

- **Columna:** Hecho
- **Descripción:** Consolida las seis fuentes, aplica el rezago de disponibilidad de las fuentes 1, 2 y 3 y marca la frescura de cada registro.
- **Paquete WBS:** 3.2 Ingesta streaming y batch
- **Requerimiento:** RF-01
- **Responsable:** Francisco Gaete
- **Estimación:** 5 h · **Real:** 5 h
- **Etiquetas:** S1, WBS 3.2
- **Evidencia:** `src/ingest.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-04 · Resolución de identidad por país

- **Columna:** Hecho
- **Descripción:** Normaliza número móvil, RUT/DNI/CC/CURP y hash de correo, valida dígito verificador y enlaza cada fuente con la solicitud. Informa lo no enlazado.
- **Paquete WBS:** 3.5 Calidad y linaje
- **Requerimiento:** RF-02
- **Responsable:** Oscar Oreste
- **Estimación:** 5 h · **Real:** 6 h
- **Etiquetas:** S1, WBS 3.5, Desviación
- **Desviación:** D2 (ver docs/desviaciones.md)
- **Evidencia:** `src/identity.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-05 · Auditoría de representatividad de la muestra

- **Columna:** Hecho
- **Descripción:** Compara la composición de la cohorte histórica con la población objetivo por zona, género, edad y sector. Respuesta temprana a RP-04.
- **Paquete WBS:** 2.4 Auditoría de sesgo
- **Requerimiento:** RF-11
- **Responsable:** Francisco Gaete
- **Estimación:** 3 h · **Real:** 3 h
- **Etiquetas:** S1, WBS 2.4
- **Evidencia:** `notebooks/01_exploracion_datos.ipynb`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-06 · Feature store precalculado

- **Columna:** Hecho
- **Descripción:** 48 variables por solicitud en parquet; la decisión solo lee una fila. Base del argumento de los 8 segundos.
- **Paquete WBS:** 3.6 Feature store
- **Requerimiento:** RF-01 · RNF-01
- **Responsable:** Oscar Oreste
- **Estimación:** 6 h · **Real:** 8 h
- **Etiquetas:** S1, WBS 3.6, Desviación
- **Desviación:** D1 (ver docs/desviaciones.md)
- **Evidencia:** `src/features.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-07 · Notebook 01 · exploración de datos

- **Columna:** Hecho
- **Descripción:** Volumen por fuente, composición por cohorte, mora real vs. registrada, calidad de identidad y rezago.
- **Paquete WBS:** 3.5 Calidad y linaje
- **Requerimiento:** RF-01
- **Responsable:** Francisco Gaete
- **Estimación:** 3 h · **Real:** 3 h
- **Etiquetas:** S1, WBS 3.5
- **Evidencia:** `notebooks/01_exploracion_datos.ipynb`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-08 · Notebook 02 · ingeniería de variables

- **Columna:** Hecho
- **Descripción:** Catálogo de variables por fuente, evidencia de exclusión digital inversa y detección de proxies.
- **Paquete WBS:** 4.1 Ingeniería de variables
- **Requerimiento:** RF-03
- **Responsable:** Oscar Oreste
- **Estimación:** 3 h · **Real:** 3 h
- **Etiquetas:** S1, WBS 4.1
- **Evidencia:** `notebooks/02_feature_engineering.ipynb`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-09 · Reporte de estado Sprint 1

- **Columna:** Hecho
- **Descripción:** Avance por paquete, hitos, desviaciones, riesgos RP materializados y decisiones.
- **Paquete WBS:** 1.2 Seguimiento y control
- **Requerimiento:** —
- **Responsable:** Francisco Gaete
- **Estimación:** 2 h · **Real:** 2 h
- **Etiquetas:** S1, WBS 1.2
- **Evidencia:** `docs/reporte_estado_sprint1.md`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante


## Sprint 2 · F3 Modelado (17-11 al 28-11-2026)

### AUR-10 · Modelo base LightGBM con split temporal

- **Columna:** Hecho
- **Descripción:** Entrena con enero a septiembre de 2025 y evalúa con octubre a diciembre. AUC, KS, matriz de confusión y curva de ganancia.
- **Paquete WBS:** 4.2 Entrenamiento y validación
- **Requerimiento:** RF-03
- **Responsable:** Francisco Gaete
- **Estimación:** 5 h · **Real:** 7 h
- **Etiquetas:** S2, WBS 4.2, Desviación
- **Desviación:** D4 (ver docs/desviaciones.md)
- **Evidencia:** `src/train.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-11 · Versionado de modelos con hash

- **Columna:** Hecho
- **Descripción:** Registro con SHA-256, fecha, variables y métricas. El motor verifica el hash antes de cargar el modelo.
- **Paquete WBS:** 4.2 Entrenamiento y validación
- **Requerimiento:** RNF-09
- **Responsable:** Oscar Oreste
- **Estimación:** 2 h · **Real:** 2 h
- **Etiquetas:** S2, WBS 4.2
- **Evidencia:** `models/registro_modelos.json`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-12 · Motor de decisión con umbrales por país

- **Columna:** Hecho
- **Descripción:** Umbral de probabilidad de incumplimiento por país leído desde params.yaml.
- **Paquete WBS:** 5.2 Umbrales por país
- **Requerimiento:** RF-04
- **Responsable:** Oscar Oreste
- **Estimación:** 3 h · **Real:** 3 h
- **Etiquetas:** S2, WBS 5.2
- **Evidencia:** `src/decision.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-13 · Explicabilidad TreeSHAP en lenguaje natural

- **Columna:** Hecho
- **Descripción:** De 3 a 5 factores que más aumentaron el riesgo en cada rechazo, redactados para la persona.
- **Paquete WBS:** 4.4 Explicabilidad
- **Requerimiento:** RF-05
- **Responsable:** Francisco Gaete
- **Estimación:** 5 h · **Real:** 6 h
- **Etiquetas:** S2, WBS 4.4
- **Evidencia:** `src/explain.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-14 · Auditoría de equidad

- **Columna:** Hecho
- **Descripción:** Tasa de aprobación, aprobación de buenos pagadores y disparate impact por género, zona, edad y sector. Criterio: 5 pp y regla del 80 %.
- **Paquete WBS:** 2.4 Auditoría de sesgo
- **Requerimiento:** RF-11
- **Responsable:** Oscar Oreste
- **Estimación:** 4 h · **Real:** 4 h
- **Etiquetas:** S2, WBS 2.4, Desviación
- **Desviación:** D3 (ver docs/desviaciones.md)
- **Evidencia:** `src/fairness.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-15 · Mitigación de sesgo y modelo v2

- **Columna:** Hecho
- **Descripción:** Reponderación de la muestra, eliminación de proxies sobre 0,35 y variables de cobertura. Ablación de cada medida.
- **Paquete WBS:** 4.3 Mitigación de sesgo
- **Requerimiento:** RF-11
- **Responsable:** Francisco Gaete
- **Estimación:** 6 h · **Real:** 8 h
- **Etiquetas:** S2, WBS 4.3, Desviación
- **Desviación:** D3 (ver docs/desviaciones.md)
- **Evidencia:** `src/train.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-16 · Benchmark de latencia contra 8 s

- **Columna:** Hecho
- **Descripción:** Ruta crítica completa sobre 2.000 solicitudes, con timeout duro de terceros. Componentes medidos y simulados declarados.
- **Paquete WBS:** 6.1 Pruebas y carga
- **Requerimiento:** RNF-01
- **Responsable:** Oscar Oreste
- **Estimación:** 3 h · **Real:** 3 h
- **Etiquetas:** S2, WBS 6.1
- **Evidencia:** `src/latency.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-17 · Monitoreo de drift PSI y KS

- **Columna:** Hecho
- **Descripción:** PSI y KS por variable y del score, y PSI mensual del score.
- **Paquete WBS:** 6.2 Panel de monitoreo
- **Requerimiento:** RF-11
- **Responsable:** Oscar Oreste
- **Estimación:** 3 h · **Real:** 3 h
- **Etiquetas:** S2, WBS 6.2
- **Evidencia:** `src/monitor.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-18 · Registro de auditoría inmutable

- **Columna:** Hecho
- **Descripción:** Cadena de hashes SHA-256 por decisión con prueba de manipulación.
- **Paquete WBS:** 5.5 Registro de auditoría
- **Requerimiento:** RF-12 · RNF-07
- **Responsable:** Francisco Gaete
- **Estimación:** 3 h · **Real:** 3 h
- **Etiquetas:** S2, WBS 5.5
- **Evidencia:** `src/audit_log.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-19 · Dashboard de monitoreo en Streamlit

- **Columna:** Hecho
- **Descripción:** Cuatro vistas: desempeño, drift, equidad con semáforo de 5 pp e inclusión efectiva.
- **Paquete WBS:** 6.2 Panel de monitoreo
- **Requerimiento:** RF-11
- **Responsable:** Oscar Oreste
- **Estimación:** 6 h · **Real:** 6 h
- **Etiquetas:** S2, WBS 6.2
- **Evidencia:** `dashboard/app.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-20 · Notebooks 03 a 05

- **Columna:** Hecho
- **Descripción:** Modelo, auditoría de equidad, latencia, monitoreo y auditoría, ejecutados con salidas.
- **Paquete WBS:** 4.2 Entrenamiento y validación
- **Requerimiento:** RF-03 · RF-11
- **Responsable:** Francisco Gaete
- **Estimación:** 4 h · **Real:** 4 h
- **Etiquetas:** S2, WBS 4.2
- **Evidencia:** `notebooks/`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-21 · Reporte de estado Sprint 2 e informe EP5

- **Columna:** Hecho
- **Descripción:** Reporte de estado, planificado vs. ejecutado, registro de desviaciones e informe.
- **Paquete WBS:** 1.2 Seguimiento y control
- **Requerimiento:** —
- **Responsable:** Francisco Gaete · Oscar Oreste
- **Estimación:** 4 h · **Real:** 5 h
- **Etiquetas:** S2, WBS 1.2, Desviación
- **Desviación:** D6 (ver docs/desviaciones.md)
- **Evidencia:** `docs/reporte_estado_sprint2.md`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-22 · Conciliación de atraso y mora con fecha efectiva

- **Columna:** Hecho
- **Descripción:** Usa la fecha efectiva de pago de corresponsales para corregir el atraso y la mora registrados con rezago (sesgo de medición).
- **Paquete WBS:** 4.3 Mitigación de sesgo
- **Requerimiento:** RF-11 · RF-01
- **Responsable:** Francisco Gaete
- **Estimación:** 0 h · **Real:** 4 h
- **Etiquetas:** S2, WBS 4.3, Agregada, Desviación
- **Desviación:** D5 (ver docs/desviaciones.md)
- **Evidencia:** `src/features.py`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante

### AUR-23 · Model card del modelo v2

- **Columna:** Hecho
- **Descripción:** Uso previsto, datos, métricas, equidad y limitaciones del modelo.
- **Paquete WBS:** 4.5 Model card
- **Requerimiento:** RF-05 · RF-11
- **Responsable:** Oscar Oreste
- **Estimación:** 2 h · **Real:** 2 h
- **Etiquetas:** S2, WBS 4.5
- **Evidencia:** `docs/model_card.md`
- **Checklist:** [x] código en el repositorio · [x] resultado en reports/ · [x] revisado por el otro integrante


## Sprint 3 · F3 Modelado (backlog replanificado)

### AUR-24 · Reject inference

- **Columna:** Backlog
- **Descripción:** Estimar el comportamiento de los rechazados históricos para corregir el sesgo de retroalimentación.
- **Paquete WBS:** 4.3 Mitigación de sesgo
- **Requerimiento:** RF-11
- **Responsable:** Francisco Gaete
- **Estimación:** 5 h · **Real:** 0 h
- **Etiquetas:** S3, WBS 4.3, Desviación
- **Desviación:** D7 (ver docs/desviaciones.md)
- **Evidencia:** `—`
