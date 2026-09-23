# Sistema de Seguimiento de Programas Minor — UFRO (2.0)

**Comience con LEEME_PRIMERO.md.** Esta versión incorpora el registro oficial de Inglés y reemplaza la clasificación automática por plazo por un estado pendiente de revisión administrativa.


Aplicación Streamlit para Inglés, Emprendimiento y Relaciones Interculturales. Incluye motor académico auditable, búsqueda individual, alertas, conciliación, Vista DIRAE XLSX, actualización de fuentes, catálogo editable y excepciones.

## Entrega

- `minor-dashboard_codigo.zip`: código listo para un repositorio **privado**. No contiene datos personales.
- `minor_snapshot_PRIVADO.zip`: paquete inicial de datos. Subir exclusivamente al Drive institucional restringido, nunca a GitHub.
- Reportes XLSX: resultados calculados al semestre 2026-2, con calificaciones disponibles hasta 2026-1. El archivo oficial de Inglés está incluido. Los casos sin respaldo de cinco asignaturas quedan fuera de la hoja principal DIRAE y aparecen en EGRESADOS POR RESPALDAR.

## Puesta en marcha

Siga `DEPLOYMENT.md`. Para producción se requieren un cliente Google OIDC, una cuenta de servicio con acceso al paquete de Drive y al menos un correo real autorizado en `[users]`. No hay cuentas reales ni secretos preconfigurados.

Para probar localmente con Python 3.12:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

Sin configuración de autenticación, la aplicación muestra sólo la pantalla de acceso restringido. Para desarrollo con datos reales, consulte la sección local de DEPLOYMENT. El modo de desarrollo está deshabilitado por defecto y requiere dos activaciones expresas.

## Actualización semestral

ADMIN → ACTUALIZAR DATOS → subir archivos acumulativos → Validar y procesar → revisar altas, retiros y estados → Guardar versión validada. Las fuentes deben conservar los encabezados originales. El archivo puede cambiar de nombre; también se acepta un nombre de hoja distinto si el Excel contiene una sola hoja.

ADMIN → CONFIGURACIÓN permite cambiar semestre, electivas/vigencias y excepciones. Al actualizar calificaciones se incorporan vigencias nuevas respaldadas por esas filas, sin sobrescribir las reglas ya revisadas. No se rellenan semestres sin evidencia. Las clasificaciones dudosas y la restricción DIFEM siguen requiriendo revisión.

La lectura queda en la sesión hasta pulsar Recargar datos. Los resultados se cachean durante 15 minutos por contenido; guardar invalida el caché. Los archivos personales nunca se sirven como recursos web estáticos.

## Límites explícitos

- OIDC y Drive están implementados, pero requieren configuración externa y una prueba de integración con las cuentas UFRO.
- Se detectan requisitos académicos; la aplicación no emite certificados oficiales. El cierre de actas y los requisitos de ingreso históricos no están plenamente acreditados por las fuentes.
- Sin descarga de movilidad/postergación, sólo se aplican excepciones registradas y aprobadas.
- No se asume equivalencia entre DIFEM y denominaciones posteriores de unidades. Confirmarla en catálogo antes de resolver los casos afectados.
- No se automatizan sistemas institucionales. Hay un protocolo para añadir posteriormente una integración autorizada.
- Un único despliegue escritor. No editar simultáneamente el paquete desde Drive o desde otra aplicación. Hay control de versión y bloqueo entre sesiones del mismo proceso; Drive no aporta una transacción distribuida en esta implementación.

## Organización

`src/`: normalización, semestres, fuentes, catálogo, motor, conciliación, DIRAE, Excel, almacenamiento, seguridad y UI.
`integrations/`: Google Drive y protocolo futuro de movimientos.
`config/`: catálogo inicial no personal y plantilla de excepciones.
`tests/`: casos académicos, seguridad, persistencia, exportación y pantallas Streamlit.

`BUSINESS_RULES.md` documenta decisiones conservadoras y fuentes. `DATA_DICTIONARY.md` documenta todas las hojas inspeccionadas. `VALIDATION_RESULTS.md` contiene resultados y pruebas de esta entrega.
