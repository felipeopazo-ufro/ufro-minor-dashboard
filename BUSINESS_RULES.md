# Reglas académicas y decisiones de implementación

## Actualización 2.0 — precedencia administrativa

Esta sección reemplaza las conclusiones automáticas incompatibles descritas más abajo, que se conservan para explicar el cálculo curricular. El motor puro calcula requisitos y plazos; `official.apply_official` decide el estado mostrado y guarda `calculated_status`, `calculated_status_reason`, `calculated_requires_review` y `calculated_graduation_semester`.

1. La columna O (Total) del avance oficial Inglés es evidencia administrativa. 5 de 5 confirma EGRESADO aunque el plazo calculado esté excedido. El sistema valida también la suma de troncales y electivas.
2. Eliminación y Renuncia son columnas propias del Minor. No se confunden con Alumno Eliminado o renuncia a la carrera. Se muestran como ELIMINADO OFICIAL / RENUNCIA OFICIAL. Datos oficiales contradictorios requieren revisión.
3. Sin eliminación oficial, un cálculo de plazo excedido se muestra como PLAZO EXCEDIDO POR REVISAR, para los tres Minor. Puede faltar respaldo histórico de prórrogas o semestres excluidos.
4. Un egreso calculado que contradice un total oficial inferior a 5 se bloquea como REQUIERE REVISIÓN.
5. La pausa académica actual no demuestra su duración. No se descuenta ningún semestre sin registro aprobado de excepción.
6. Un registro oficial sólo se aplica a una participación de Inglés inequívoca por matrícula. Sin coincidencia o con reinscripción ambigua queda visible en VALIDACIÓN, sin alta ni asociación automática. El indicador oficial cuenta todos los registros del archivo; los indicadores de participaciones cuentan el padrón de inscritos.
7. Se preserva la fecha oficial de Plan Completo por separado. No se transforma una fecha administrativa en semestre académico ni se inventa un egreso para los 5/5 sin fecha.
8. La hoja DIRAE exige `dirae_ready`: egreso calculado válido, sin conflictos y sin contradicción oficial. Un 5/5 que sólo demuestra finalización administrativa no autoriza inventar cinco filas; aparece en EGRESADOS POR RESPALDAR hasta conciliar notas/excepciones.
9. Las eliminaciones por troncal calculadas conservan su origen CÁLCULO. La vista ELIMINADOS permite distinguirlas de las oficiales.
10. El registro oficial es una foto de la última descarga. No se utiliza para reconstrucción retrospectiva si cambia el semestre de corte.

## Prórrogas extraordinarias y retiro temporal

Se aceptan tipos Movilidad, Postergación, Retiro temporal y Prórroga extraordinaria. Los tres primeros excluyen un semestre aprobado con contabiliza_en_plazo=NO. Una prórroga añade el entero positivo semestres_extension al plazo, una sola vez por combinación semestre_afectado + observacion. Para una prórroga, semestre_afectado es el semestre de autorización; observacion debe identificar su respaldo. Siempre exige aprobada=SI. No se crean prórrogas automáticamente por existir 5/5 oficial. Las fechas y períodos exactos deben documentarse.

## Cálculo curricular de base


## Precedencia

1. Reglas explícitas del encargo: aplicables a los tres Minor y prioritarias frente a divergencias de redacción.
2. Reglamentos adjuntos, artículos 3, 5, 6 y 7.
3. Evidencia histórica de calificaciones y seguimiento para catálogo por semestre.
4. Seguimiento anterior como contraste, no como autoridad sobre estados.

## Universo e identidad

Sólo Inscritos determina pertenencia. Una participación es matrícula + Minor + semestre de inscripción. Matrícula es texto: se normalizan espacios y .0 accidental sin convertir a float. Las inscripciones exactamente repetidas no crean otra participación, pero se reportan. Inscripciones en dos Minor se evalúan independientemente. Reinscripciones en el mismo Minor quedan en revisión para no revivir una eliminación anterior automáticamente.

Nombre/carrera: padrón máster, seguimiento, calificaciones más recientes, inscritos. Se informa la fuente elegida y todas las variantes incompatibles. Diferencias de mayúsculas/tildes/espacios no son conflictos. Nombres diferentes bloquean el caso. Carreras diferentes bloquean Emprendimiento si cambian la aplicación de la restricción especial; el resto se informa como advertencia. Una carrera/nombre ausente también exige revisión. El padrón activo no elimina históricos.

## Requisitos y semestre

Dos troncales distintas y tres electivas distintas por código. Troncales:

| Minor | Códigos |
|---|---|
| Inglés | DFI183, DFI185 |
| Emprendimiento | DFI165, IAE145 |
| Relaciones Interculturales | DFI300, DFI310 |

El ordinal es año × 2 + semestre − 1. Plazo ordinario: ordinal de inscripción + 5. El semestre de inscripción cuenta como primero. Una inscripción 2024-2 vence en 2027-1. Estar en el sexto semestre no elimina: CURSANDO con alerta CRÍTICA. El semestre siguiente se elimina por plazo si no se completó.

Troncales y electivas aprobadas: desde cuatro semestres anteriores a la inscripción hasta el límite. El borde de cuatro semestres se incluye; cinco se excluye. Una reprobación troncal previa no se interpreta como intento dentro de esa participación. Los códigos CIP040, CIP044, CIP101, CIP105, CIP140, CIP147, CIP159, CIP163, CIP165, CIP171, CIP183 y CIP185 corresponden a DFI con el mismo número. Se conservan código original y canónico; cada asignatura canónica cuenta una vez. Los pares con nombres distintos quedan bloqueados y reportados para revisión.

## Intentos, notas e incertidumbre

Se agrupan registros por matrícula, código y semestre. Coincidencias exactas de nota/estado cuentan una sola vez; se conserva el número de registros y la fila de origen representativa. Diferencias de nota o estado en ese grupo se consideran intentos ambiguos y bloquean la participación. No se fuerza un aprobado sobre un reprobado contradictorio.

Las fuentes entregan APROBADA/REPROBADA; ese campo determina el resultado. La escala 1–7 y el umbral 4,0 sólo se usan como control técnico de coherencia, no para inventar estados ausentes. Si cambia la escala institucional deberá modificarse y probarse esa validación técnica; en esta versión no existe fallback por nota. Un estado ausente/desconocido queda en revisión.

Una reprobación troncal durante la participación elimina aunque exista aprobación posterior. Una reprobación posterior al semestre en que ya se completó válidamente el programa no revoca ese egreso. En el mismo semestre, la reprobación prevalece porque no hay fechas de acta para establecer otro orden. Electivas reprobadas no eliminan.

No se cuentan asignaturas posteriores al semestre de corte. Las asignaturas después del plazo permanecen visibles: si completan el conjunto sin excepción se informa `completed_out_of_time=true`, pero no se declara egreso.

## Selección determinista y egreso

Primera aprobación válida de cada código; electivas ordenadas por semestre y código. Se seleccionan las primeras tres. El semestre de egreso es el máximo entre las dos troncales y las tres electivas elegidas. Las demás aparecen como adicionales o aprobaciones repetidas. DIRAE incluye exactamente esas cinco filas únicamente para EGRESADO sin revisión.

`counted_for_completion` muestra el avance de requisitos; puede ser verdadero para una asignatura de una participación eliminada. No equivale por sí solo a autorización de certificado. DIRAE aplica además el estado global.

## Catálogo y Emprendimiento

920 filas iniciales de catálogo, construidas desde ambos registros académicos y las troncales normativas. Las electivas tienen vigencia del semestre observado, sin extender intervalos a semestres no documentados. Una clasificación contradictoria queda no confirmada. Una asignatura puede tributar a más de un Minor si existe evidencia en ambos.

Para Ingeniería Comercial y Contador Público y Auditor, el reconocimiento de electivas se decide mediante la unidad consignada en las fuentes y la aclaración institucional de que la oferta de Formación General satisface la restricción:

- DIFEM o Coordinación de Formación General e Idiomas → SI;
- unidad departamental distinta de DIFEM → NO;
- unidad no identificable o mezcla incompatible → REVISAR.

IAE145 sigue siendo troncal válida. Los campos `valida_ing_comercial` y `valida_contador_auditor` pueden confirmarse en CONFIGURACIÓN con respaldo. Un código desconocido o clasificación dudosa en el período relevante obliga a revisión, incluso si hay otras asignaturas suficientes; es una política conservadora de esta versión.

## Excepciones

Campos: matrícula, Minor, enrollment_id opcional sólo cuando hay una participación inequívoca, semestre_afectado, tipo_excepcion, observacion, contabiliza_en_plazo, aprobada. Tipos originales: Movilidad/Postergación; ampliados en la sección 2.0 anterior. Sin aprobación y respaldo no se extiende plazo.

Se excluyen semestres distintos, no filas: una excepción duplicada no duplica extensión. El cálculo itera porque la extensión puede incorporar otro semestre excluido. Excepciones anteriores al ingreso o posteriores al límite ya extendido no reviven la participación. Un semestre futuro dentro de la ventana puede extenderla si ya existe aprobación registrada; no se inventan excepciones desde notas históricas de postergación.

## Orden de estados

1. Incertidumbre material → REQUIERE REVISIÓN.
2. Reprobación troncal previa al egreso → ELIMINADO POR TRONCAL.
3. Requisitos completos dentro del plazo → EGRESADO.
4. Semestre actual posterior al límite → ELIMINADO POR PLAZO.
5. Pendiente dentro del plazo → CURSANDO.

La incertidumbre tiene prioridad para evitar decisiones irreversibles sobre registros contradictorios. Alertas sólo para CURSANDO: penúltimo semestre PREVENTIVA, último CRÍTICA.

## Reglamento completo: aspectos fuera del cálculo automático

Los reglamentos establecen unidades responsables y coordinación; oferta electiva modificable; evaluación anual de calidad; inscripción por cupos; condiciones de alumno regular; requisitos de nivel de carrera (Inglés e Interculturales: segundo a sexto; Emprendimiento: máximo sexto); y suficiencia de inglés previa para el Minor en Inglés. También establecen certificado separado del título y solicitado tras cierre de actas.

Las fuentes no prueban el nivel histórico al ingreso, todas las fechas de suficiencia, todos los semestres regulares ni el cierre formal de cada acta. El padrón 2026 no se usa para reconstruir retroactivamente esa evidencia. La inscripción oficial se acepta como antecedente de admisión; no se elimina a alguien por ausencia de evidencia histórica. Egresado significa cumplimiento curricular calculado, sujeto a validación administrativa para certificado.

Los artículos 4 y 8 (aseguramiento de calidad, cupos y proceso de inscripción) se documentan pero no se inventa su cumplimiento. La hoja Placement Test se inspeccionó y queda como antecedente de referencia, no como requisito adicional de egreso.

La redacción de Emprendimiento sobre convalidación previa a la primera versión se reemplaza, por instrucción expresa, por cuatro semestres anteriores a cada inscripción en los tres programas.

## Conciliación

Se compara por matrícula + Minor + semestre de inscripción. Se informan coincidencias, diferencias de estado/egreso/códigos y cantidades, casos sólo nuevos y sólo antiguos. Los casos con el mismo estudiante pero distinta inscripción/Minor aparecen en los exclusivos, con candidatos nuevos para revisar. El conteo histórico incluye códigos registrados, no necesariamente aprobaciones válidas. No se interpreta esa diferencia automáticamente como error del sistema nuevo.

Los 701 registros antiguos con “No inscrito” no son semestres malformados a corregir: se reportan como información. Ninguno se incorpora por tener notas compatibles.


## Inscripciones actuales del semestre

La fuente privada `current_enrollments.xls` se reemplaza en cada actualización semestral. Sólo el valor normalizado `Inscrita` produce una fila `CURSANDO`. Se vincula por matrícula + participación Minor + código. Se acepta una troncal obligatoria o una electiva previamente confirmada en el catálogo de ese Minor; un código nuevo o perteneciente a otro Minor queda en VALIDACIÓN. La inscripción actual puede respaldar la oferta de un código ya confirmado para el semestre cargado, pero nunca crea por sí sola una nueva pertenencia al Minor ni una vigencia futura.

Las filas `CURSANDO` se anexan después del cálculo académico y no tienen nota, estado final, ni `counted_for_completion`. No modifican `total_completed`, ratios aprobados, egreso, eliminación por troncal ni la exportación DIRAE. En Buscar Estudiante se muestran separadas del avance aprobado dentro de “HISTORIAL DE ASIGNATURAS DEL MINOR”, junto con aprobadas, reconocidas previas, reprobadas y aprobadas adicionales. La tabla visible oculta los indicadores técnicos de conteo.

El padrón maestro más reciente es prioritario para nombre, carrera y condición universitaria actual. La falta de un registro en ese padrón genera un hallazgo cuando corresponde al ingreso del semestre actual; nunca elimina una participación histórica ni cambia su estado académico.
