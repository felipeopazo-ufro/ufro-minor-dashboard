# Validación de fuente actual de inscripciones 2026-2

Actualización de la candidata `academic-engine-final`, PR #1. Paquete privado con el máster del 29-09-2026, inscripciones actuales en clave estable `current_enrollments.xls` y evidencia de oferta 2026-2 sólo para códigos previamente confirmados.

- Suite completa: 122 pruebas aprobadas, incluidas las 105 preexistentes y 17 pruebas nuevas de inscripciones actuales e historial visible.
- Cruce de ingresos 2026-2: 79 participaciones (Inglés 65, Emprendimiento 9, Interculturales 5); 75 con al menos una asignatura confirmada de su Minor (62, 8, 5); 4 sin asignatura propia detectada.
- Máster vigente: 78 de las 79 participaciones. Una ausencia genera hallazgo de validación y conserva la participación.
- Fuente actual: 3.450 filas, todas con `Inscrita`; sin matrículas vacías ni duplicados matrícula/código en el archivo recibido.
- Resultados históricos de control: Emprendimiento 170 egresados (4 con probable excepcionalidad); Inglés 365 egresados (15 con probable excepcionalidad, 18 en revisión).
- Las filas `CURSANDO` se anexan luego del cálculo, sin nota ni resultado académico; no cambian progreso, egreso, eliminación ni DIRAE.
- AppTest recorre las ocho pantallas con el paquete privado local, incluida búsqueda y tabla unificada del historial; no se modifican autenticación, Drive ni navegación.

## Validación anterior de la versión 2.0

Semestre de cálculo: 2026-2. Fuentes originales más Avances Minor Inglés(1).xls. El registro oficial tiene 653 estudiantes y 351 completados.

## Pruebas y resultados

**65 pruebas aprobadas** en 47,66 segundos, incluida carga del paquete privado actualizado y navegación de las ocho pantallas.

La suite verifica lógica académica, acceso cerrado, roles, persistencia local, carga oficial y control de columnas/totales, prioridad administrativa, eliminación/renuncia, contradicciones, exclusión de DIRAE sin respaldo, registros sin inscripción única, pausas sin duración inventada, prórrogas extraordinarias y las ocho páginas de Streamlit con los datos reales.

La verificación real conserva 1.124 participaciones. Corrige 34 eliminaciones calculadas por plazo a egreso oficial. No crea inscripciones nuevas: hay dos personas oficiales sin coincidencia, una de ellas con 5/5, y otra matrícula con dos participaciones de Inglés que no se asigna automáticamente. El panel oficial cuenta las 653 personas; los indicadores de participaciones conservan el padrón.

| Estado de participación | Cantidad |
|---|---:|
| EGRESADO | 453 |
| CURSANDO | 392 |
| PLAZO EXCEDIDO POR REVISAR | 143 |
| REQUIERE REVISIÓN | 106 |
| ELIMINADO OFICIAL | 17 |
| PAUSA ACADÉMICA REGISTRADA | 6 |
| ELIMINADO POR TRONCAL | 5 |
| RENUNCIA OFICIAL | 2 |

350 de los 351 completados oficiales están vinculados inequívocamente. El caso restante se muestra en VALIDACIÓN. Las 453 participaciones EGRESADO incluyen los tres Minor y no equivalen a certificados emitidos.

La Vista DIRAE tiene 412 participaciones listas y 2.060 filas (cinco cada una). Otros 41 egresos están reconocidos oficialmente, pero su respaldo de asignaturas requiere conciliación: se muestran en EGRESADOS POR RESPALDAR. No se inventaron fechas de egreso, notas ni extensiones.

17 eliminaciones y 2 renuncias provienen de columnas administrativas oficiales del Minor. Las 5 eliminaciones por troncal restantes tienen origen de cálculo explícito. Los 143 plazos excedidos por revisar no se presentan como eliminaciones oficiales.

El paquete de código no contiene datos personales ni secretos. El paquete privado conserva originales, catálogo, excepciones, configuración y auditoría.

La integración con Google OIDC y Drive continúa pendiente de credenciales externas. Las pruebas de aplicación son locales; no se afirma que ya esté desplegada.

## Antecedente de la versión inicial (superado por esta entrega)

### Resultados iniciales de referencia

Fecha: 23 septiembre 2026. Semestre de corte: 2026-2. Notas disponibles hasta 2026-1. Sin excepciones manuales iniciales.

## Pruebas

42 pruebas automatizadas aprobadas con pytest. Incluyen los 13 escenarios académicos solicitados, límites de semestre, duplicados, incertidumbre, selección determinista, autenticación/roles, conservación de versiones, rechazo de estructura inválida y exportación XLSX con identificadores de texto y protección contra fórmulas incrustadas.

Streamlit AppTest recorrió las ocho pantallas con los datos reales: PANORAMA, BUSCAR ESTUDIANTE (incluida búsqueda), VISTA DIRAE, ELIMINADOS, ALERTAS, VALIDACIÓN, ACTUALIZAR DATOS y CONFIGURACIÓN. También se probó el bloqueo de acceso sin credenciales. La fixture privada no se distribuye dentro del código; la prueba real se ejecuta si se coloca el paquete en data/private/minor_snapshot.zip.

Se inició además el servidor Streamlit local y su endpoint de salud respondió HTTP 200 (ok). La autenticación Google real, la escritura en Drive y la publicación en Community Cloud quedan pendientes de las credenciales y permisos institucionales. No se simularon como pruebas externas exitosas.

## Resultados iniciales

1.124 participaciones de 1.122 personas. No se añadió a nadie por tener calificaciones sin inscripción.

| Estado | Participaciones |
|---|---:|
| EGRESADO | 417 |
| CURSANDO | 399 |
| ELIMINADO POR PLAZO | 194 |
| REQUIERE REVISIÓN | 109 |
| ELIMINADO POR TRONCAL | 5 |

Vista DIRAE preliminar: 417 participaciones, 2.085 filas. Se verificó que cada egreso tenga cinco códigos distintos, dos troncales y tres electivas, sin revisión y dentro del plazo. Matrículas se preservan como texto. Todos los reportes Excel se reabrieron para comprobar estructura, filtros/tablas, encabezados congelados y ausencia de fórmulas inesperadas; se revisaron vistas renderizadas de sus 14 hojas.

Los 109 casos pendientes no se certifican automáticamente. Son resultados provisionales sujetos a resolver discrepancias y a registrar movilidad/postergaciones aprobadas que no vienen en las descargas. Los 417 egresos representan cumplimiento curricular calculado, no emisión oficial de certificados.

## Comparación con seguimiento

| Indicador | Cantidad |
|---|---:|
| Participaciones nuevas | 1124 |
| Participaciones históricas | 1641 |
| Coincidencias de participación | 952 |
| Sólo nueva base | 172 |
| Sólo seguimiento anterior | 689 |
| Diferencias de estado | 280 |
| Diferencias de asignaturas | 391 |
| Diferencias de egreso | 200 |

La comparación usa participación completa, no sólo persona. Por eso 689 participaciones sólo antiguas no equivale a las 652 personas sólo antiguas. Las coincidencias de persona con inscripción/Minor diferentes quedan visibles para revisión.

## Calidad de datos

| Hallazgo | Registros |
|---|---:|
| Histórico sin inscripción | 701 |
| Sólo seguimiento | 652 |
| Conflicto carrera | 130 |
| Participación requiere revisión | 109 |
| Inscrito sin calificaciones | 74 |
| Conflicto nombre | 30 |
| Duplicado técnico | 26 |
| Catálogo pendiente | 11 |
| Nota/estado inválido | 4 |

Los hallazgos no se suman como personas: un estudiante puede tener más de un problema. Los 701 registros históricos dicen expresamente No inscrito, por lo que se clasifican como información. Las cuatro notas fuera de escala son 0; no se reinterpretan como 1 ni se inventa una aprobación.

## Decisiones pendientes antes de uso administrativo

- Confirmar equivalencia DIFEM / Coordinación de Formación General e Idiomas y reflejarla en las vigencias afectadas del catálogo, especialmente para Ingeniería Comercial y Contador Público y Auditor.
- Revisar los conflictos de identidad y las clasificaciones dudosas.
- Incorporar movilidad/postergaciones con respaldo y aprobación.
- Verificar cierre de actas con DIRAE.

Estas decisiones se resuelven mediante las fuentes y la configuración; no requieren reescribir gráficos o fórmulas.

## Versiones verificadas

Python 3.12. Dependencias fijadas para reproducibilidad:

```text
streamlit==1.64.0
pandas==2.2.3
openpyxl==3.1.5
Authlib==1.8.0
google-api-python-client==2.200.0
google-auth==2.58.0
pytest==9.1.1
```
