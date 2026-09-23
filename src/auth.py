import os
PAGES={'ADMIN':['PANORAMA','BUSCAR ESTUDIANTE','VISTA DIRAE','ELIMINADOS','ALERTAS','VALIDACIÓN','ACTUALIZAR DATOS','CONFIGURACIÓN'],'GESTION':['PANORAMA','BUSCAR ESTUDIANTE','VISTA DIRAE','ELIMINADOS','ALERTAS'],'CONSULTA':['PANORAMA','BUSCAR ESTUDIANTE'],'DIRAE':['VISTA DIRAE']}
def role_for(user,allowlist):
    email=str(user.get('email','')).strip().lower()
    if user.get('email_verified') is not True or not email.endswith('@ufrontera.cl'):return None
    role=allowlist.get(email)
    return role if role in PAGES else None

def authenticate(st,settings):
    dev=settings.get('app',{}).get('development_mode',False)
    if dev and os.environ.get('MINOR_LOCAL_DEVELOPMENT')=='1' and settings.get('storage',{}).get('mode')=='LOCAL':
        st.warning('DESARROLLO LOCAL · autenticación deshabilitada explícitamente')
        return 'ADMIN','desarrollo-local'
    if 'auth' not in settings:
        st.info('Acceso restringido. Falta configurar la autenticación institucional.');st.stop()
    if not st.user.is_logged_in:
        st.write('Ingrese con una cuenta institucional autorizada.')
        if st.button('Ingresar con Google'):st.login()
        st.stop()
    role=role_for(st.user.to_dict(),dict(settings.get('users',{})))
    if not role:
        st.error('Su cuenta no está autorizada para ingresar.')
        if st.button('Cerrar sesión'):st.logout()
        st.stop()
    if st.sidebar.button('Cerrar sesión'):st.logout()
    return role,st.user.email

def require_admin(role):
    if role!='ADMIN':raise PermissionError('Esta operación requiere rol ADMIN.')
