# Despliegue en Streamlit Community Cloud — versión 2.0

Empiece por **LEEME_PRIMERO.md**, incluido en el ZIP. El paquete privado actualizado ya incorpora el avance oficial del Minor en Inglés.

**Si ya tiene una instalación con excepciones o catálogo editados:** actualice el código y cargue solamente el archivo oficial desde ACTUALIZAR DATOS. No sustituya su paquete completo por el inicial, pues perdería sus cambios. Si aún no ha hecho cambios, puede usar el paquete actualizado directamente.


## 1. Preparar archivos

Descomprima `minor-dashboard_codigo.zip`. La carpeta del proyecto debe contener `app.py`, `requirements.txt`, `src/`, `config/` y `.streamlit/`.
Mantenga `minor_snapshot_PRIVADO.zip` fuera de la carpeta que subirá a GitHub. Contiene datos académicos identificables.

## 2. Crear el repositorio privado

1. Ingrese a https://github.com/new con la cuenta que administrará el sistema.
2. Nombre sugerido: `ufro-minor-dashboard`. Seleccione **Private** y cree el repositorio.
3. Suba únicamente el contenido del paquete de código. Incluya `.gitignore` y `.streamlit/config.toml`. No suba el paquete de datos ni reportes.
4. Si usa Git, desde la carpeta del código:

```bash
git init
git add .
git status
# Revise que no aparezcan datos, reportes, secretos ni credenciales.
git commit -m "Sistema Minor UFRO"
git branch -M main
git remote add origin https://github.com/SU-USUARIO/ufro-minor-dashboard.git
git push -u origin main
```

El repositorio almacena el programa y permite que Streamlit lo instale y actualice. Las calificaciones y el padrón se leen desde Drive.

## 3. Google Drive y cuenta de servicio

1. En https://console.cloud.google.com/ seleccione o cree un proyecto institucional autorizado.
2. APIs y servicios → Biblioteca → habilite **Google Drive API**.
3. IAM y administración → Cuentas de servicio → Crear cuenta de servicio. No es necesario concederle un rol amplio sobre el proyecto para leer Drive.
4. Abra la cuenta → Claves → Agregar clave → Crear clave JSON. Guarde el archivo en un lugar privado. Si la institución restringe claves, solicite al administrador el mecanismo permitido; no eluda esa política.
5. En Google Drive cree una carpeta restringida, preferentemente en una unidad compartida institucional. Desactive cualquier acceso mediante enlace público.
6. Suba manualmente `minor_snapshot_PRIVADO.zip` a esa carpeta. Comparta sólo ese archivo o carpeta con el `client_email` de la cuenta de servicio, con permiso **Editor** para actualizarlo. Si la institución impide compartir con cuentas de servicio, el administrador deberá habilitar una vía autorizada.
7. Abra el archivo y copie su ID: la cadena entre `/d/` y `/view` en su enlace. Se usa como `snapshot_file_id`; no es el ID de la carpeta.
8. El programa sólo lee y actualiza ese archivo existente. No crea archivos propiedad de la cuenta de servicio. Las cuentas de servicio no tienen cuota propia; por eso el paquete se carga manualmente o reside en una unidad compartida.
9. Guarde una copia inicial privada. Las actualizaciones solicitan conservar la revisión anterior de Drive. Drive limita las revisiones conservadas; archive/depure versiones antiguas administrativamente cuando corresponda, antes de alcanzar la cuota.

Se usa el alcance API `drive` porque el archivo fue creado manualmente, no por un selector OAuth de la aplicación. Los permisos efectivos siguen limitados a los recursos compartidos con esa cuenta. Utilice una cuenta de servicio dedicada y comparta sólo la carpeta necesaria.

## 4. Crear aplicación en Streamlit

1. Ingrese a https://share.streamlit.io/ y conecte GitHub. Autorice acceso al repositorio privado.
2. Create app → Deploy a public app from GitHub / opción de despliegue desde repositorio (las etiquetas pueden variar).
3. Seleccione su repositorio privado, rama `main`, archivo `app.py`, Python **3.12** y un subdominio disponible, por ejemplo `ufro-minor-interno`.
4. Mantenga la aplicación privada mediante la configuración de uso compartido de Community Cloud. Una cuenta puede requerir autorización tanto en esa capa como en la lista `[users]` de la aplicación.
5. Antes del uso operativo, configure los secretos del siguiente apartado. Sin ellos, la aplicación permanece cerrada y no carga datos.

## 5. Google Authentication / OIDC

1. En Google Cloud abra **Google Auth Platform**. Configure Branding: nombre de la app y correo de soporte institucional.
2. Audience: seleccione **Internal** si el proyecto pertenece a la organización Google Workspace UFRO. Si sólo puede usar External, use el modo de pruebas y agregue explícitamente los usuarios de prueba mientras su administrador define la configuración institucional.
3. Clients → Create client → Web application.
4. En Authorized redirect URIs agregue exactamente:
   `https://SU-SUBDOMINIO.streamlit.app/oauth2callback`
5. Para pruebas locales agregue además `http://localhost:8501/oauth2callback`.
6. Copie Client ID y Client secret. No los suba a GitHub.
7. La autenticación valida Google OIDC. La autorización exige `email_verified=true`, sufijo exacto `@ufrontera.cl` y coincidencia en `[users]`. Cuentas de alumnos `@ufromail.cl` no se autorizan.

## 6. Secretos de Streamlit

En Advanced settings durante despliegue o App settings → Secrets, copie el contenido de `.streamlit/secrets.toml.example` y reemplace TODOS los valores de ejemplo.

- `[app] development_mode = false`.
- `[storage] mode = "GOOGLE_DRIVE"` e ID real del archivo ZIP.
- `[auth] redirect_uri`, `client_id`, `client_secret` y `cookie_secret` aleatorio. Genere este último con:
  `python -c "import secrets; print(secrets.token_hex(32))"`.
- `[google_service_account]`: copie los campos del JSON de la cuenta. La clave privada debe conservar sus saltos de línea dentro de triple comilla TOML.
- `[users]`: sustituya `administrador@ufrontera.cl` por el correo real del responsable. Ejemplo de sintaxis: `"correo.real@ufrontera.cl" = "ADMIN"`. No se ha supuesto el correo del usuario.

Roles: ADMIN (todas las operaciones), GESTION (seguimiento y exportaciones), CONSULTA (panorama y búsqueda sin exportación XLSX), DIRAE (sólo la vista de certificación). Los cambios de lista/rol se aplican en la siguiente ejecución de la sesión; reinicie la aplicación después de revocar accesos activos.

Guarde y despliegue. Si cambia subdominio, actualice tanto la URI de Google como `redirect_uri`.

## 7. Verificación de puesta en servicio

1. Abra la app sin sesión: sólo debe ver acceso restringido.
2. Ingrese con su cuenta autorizada. Revise que PANORAMA muestre semestre 2026-2 y 1.124 participaciones del paquete inicial. El panel oficial Inglés debe indicar 653 estudiantes y 351 completados; el total oficial incluye un completado pendiente de vincular a Inscritos.
3. Pruebe con un correo institucional no incluido en `[users]`: debe denegarse.
4. Pruebe CONSULTA y DIRAE para comprobar alcance de páginas.
5. ADMIN → CONFIGURACIÓN: compruebe catálogo y excepciones vacías iniciales.
6. Descargue una Vista DIRAE y confirme cinco filas por participación, dos troncales y tres electivas.
7. Pruebe una actualización autorizada, reinicie la app y pulse Recargar datos: debe recuperar lo guardado en Drive.
8. Revise primero los casos pendientes y la equivalencia de unidades. La prueba de login real, permisos institucionales y escritura en Drive no puede completarse sin estas credenciales.

## 8. Pruebas locales

Copie el paquete privado a `data/private/minor_snapshot.zip` dentro de la carpeta local. Cree `.streamlit/secrets.toml` con:

```toml
[app]
development_mode = true
[storage]
mode = "LOCAL"
local_path = "data/private/minor_snapshot.zip"
```

PowerShell:
```powershell
$env:MINOR_LOCAL_DEVELOPMENT="1"
python -m streamlit run app.py --server.address 127.0.0.1
```
Linux/macOS:
```bash
MINOR_LOCAL_DEVELOPMENT=1 python -m streamlit run app.py --server.address 127.0.0.1
```

No habilite esta combinación en un servidor compartido. Para producción vuelva a `development_mode=false` y GOOGLE_DRIVE. Nunca agregue secrets.toml o data/ a Git.

Si necesita reconstruir el paquete desde los cuatro Excel:
```bash
python bootstrap.py --input RUTA_A_CARPETA_EXCEL
```
Esto reconstruye el catálogo desde evidencia original y deja excepciones vacías. No se utiliza para las actualizaciones habituales: éstas conservan configuración, excepciones y auditoría desde la interfaz.

## 9. Recuperación y actualización

Un archivo inválido no se guarda. La previsualización muestra altas, retiros y nuevos estados. Al guardar, el paquete completo sustituye la versión anterior. Cambios simultáneos desde la misma aplicación se detectan con versión y bloqueo; no use dos despliegues escritores ni edite el ZIP simultáneamente en Drive.

Para revertir: detenga las actualizaciones, restaure la versión deseada en el historial de versiones del archivo Drive y reinicie/recargue la app. En modo local existen respaldos en `data/private/backups/`.

No se cuenta con persistencia en el disco de Community Cloud. Drive es la fuente de verdad. Las sesiones y cachés son temporales.

## Fuentes técnicas consultadas

- https://docs.streamlit.io/develop/tutorials/authentication/google
- https://docs.streamlit.io/develop/concepts/connections/authentication
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- https://docs.streamlit.io/develop/concepts/connections/connecting-to-data
- https://developers.google.com/workspace/drive/api/guides/handle-errors

Verificación documental: 23 septiembre 2026. Las etiquetas de las consolas pueden cambiar.
