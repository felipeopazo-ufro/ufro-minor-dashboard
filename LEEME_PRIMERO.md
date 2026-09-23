# Cómo seguir — versión 2.0

La aplicación está construida y probada localmente. Aún falta publicarla con sus cuentas institucionales. Los pasos externos requieren que usted inicie sesión; no envíe contraseñas o claves privadas por el chat.

## Archivos que necesita

1. **minor-dashboard_codigo.zip**: programa completo. Descomprima y suba a un repositorio privado de GitHub sólo el contenido de la carpeta `minor-dashboard`.
2. **minor_snapshot_PRIVADO.zip**: datos reales actualizados, incluido el archivo oficial de Inglés. No descomprima para subir a Drive; no lo suba a GitHub.
3. **Guia_despliegue_Minor.md**: guía detallada para Google y Streamlit. Dentro del código también se llama DEPLOYMENT.md.

## Si aún no ha publicado nada

1. Cree su cuenta de GitHub si no tiene una. En https://github.com/new cree `ufro-minor-dashboard` y marque **Private**.
2. Suba los archivos del código, incluidos `.streamlit/config.toml` y `.gitignore`. En la raíz del repositorio debe verse `app.py`, no el ZIP ni una carpeta adicional que lo oculte.
3. En Google Drive institucional cree una carpeta restringida y suba `minor_snapshot_PRIVADO.zip`.
4. En Google Cloud configure una cuenta de servicio con permiso para leer/actualizar ese archivo, y un cliente de acceso Google para la aplicación. Son configuraciones distintas: una accede a Drive y la otra identifica a las personas. DEPLOYMENT.md indica cada campo.
5. En https://share.streamlit.io/ conecte el repositorio privado, seleccione `main`, `app.py`, Python 3.12 y un nombre para su sitio. Mantenga el acceso privado en las opciones de uso compartido.
6. Copie la plantilla `.streamlit/secrets.toml.example` al apartado Secrets y sustituya los ejemplos: ID del paquete Drive, credenciales Google y correos institucionales autorizados. Mantenga `development_mode=false`.
7. Registre en Google la dirección exacta `https://SU-APP.streamlit.app/oauth2callback`. Ingrese con su cuenta autorizada y compruebe el panel oficial Inglés: 653 estudiantes, 351 con 5/5.

El primer paso práctico es el repositorio privado de GitHub. La configuración de Google puede requerir apoyo de informática si la institución restringe la creación de proyectos, claves o cuentas de servicio.

## Si ya había desplegado la versión anterior

1. Actualice el código del repositorio privado con el contenido del ZIP nuevo. No cambie sus secretos reales por la plantilla.
2. Si NO ha hecho cambios manuales en la aplicación, suba el paquete privado actualizado como **nueva versión del mismo archivo Drive**, para conservar su ID. También puede subirlo como archivo nuevo y cambiar `snapshot_file_id` en Secrets.
3. Si YA registró excepciones o modificó el catálogo en la versión anterior, **conserve su paquete actual**: después de actualizar el código, entre a ACTUALIZAR DATOS y suba sólo `Avances Minor Inglés(1).xls` en el nuevo campo de avance oficial. Valide y guarde. Así conserva catálogo, excepciones y auditoría existentes.
4. Reinicie la aplicación en Streamlit si no se ha reiniciado sola y pulse Recargar datos.
5. Compruebe las cifras oficiales y consulte VALIDACIÓN para los casos sin vinculación única.

## Qué cambió

- El 5/5 oficial de Inglés confirma egreso, con independencia del plazo ordinario calculado.
- Se conserva el estado calculado para explicar diferencias; las notas originales no se modifican.
- Se separan eliminación oficial, renuncia oficial y plazo excedido por revisar.
- Se reconocen pausas académicas actuales sin inventar su duración.
- Puede registrar Movilidad, Postergación, Retiro temporal y Prórroga extraordinaria con respaldo y aprobación. Para la última, complete `semestres_extension`.
- El exportable DIRAE exige cinco asignaturas identificadas. Egresos oficiales sin ese respaldo quedan en una hoja separada.
- El registro oficial no reemplaza automáticamente la inscripción: los dos estudiantes sin coincidencia y una matrícula con dos participaciones de Inglés quedan visibles en VALIDACIÓN. Uno de los dos no vinculados tiene 5/5; se incluye en el total oficial de 351, pero no se agrega silenciosamente al padrón.

## Actualizaciones futuras

Cada semestre: ACTUALIZAR DATOS → cargar bases acumulativas y, cuando corresponda, el avance oficial de Inglés → Validar y procesar → revisar → Guardar versión validada.

CONFIGURACIÓN permite actualizar semestre, catálogo y excepciones. Este sistema no reemplaza el trámite de certificación de DIRAE. El resumen oficial muestra la última descarga cargada; no es una reconstrucción retroactiva del estado oficial al cambiar el semestre de corte.
