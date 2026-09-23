from pathlib import Path
import streamlit as st
from src.auth import authenticate,PAGES
from src.storage import make_storage
from src import ui
st.set_page_config(page_title='Minor UFRO',page_icon='🎓',layout='wide')
st.title('Sistema de Seguimiento de Programas Minor')
st.caption('Universidad de La Frontera · Formación General e Idiomas')
try:settings=st.secrets.to_dict()
except Exception:settings={}
role,actor=authenticate(st,settings)
st.sidebar.caption(f'{actor} · {role}')
page=st.sidebar.radio('Navegación',PAGES[role])
try:
    storage=make_storage(settings)
    if st.sidebar.button('Recargar datos'):st.session_state.pop('snapshot',None)
    if 'snapshot' not in st.session_state:
        with st.spinner('Cargando fuentes autorizadas…'):st.session_state.snapshot=storage.read()
    files,version=st.session_state.snapshot
    with st.spinner('Calculando trayectorias…'):r,sources=ui.compute(files)
    if 'avance_oficial_ingles.xlsx' not in files:st.warning('No se ha cargado el avance oficial de Inglés. ADMIN puede incorporarlo en ACTUALIZAR DATOS.')
    st.sidebar.caption('Versión 2.0 · avance oficial integrado')
    st.sidebar.caption(f'Semestre actual: {r["current"]}')
    st.subheader(page)
    if page=='PANORAMA':ui.panorama(r,role)
    elif page=='BUSCAR ESTUDIANTE':ui.search(r)
    elif page=='VISTA DIRAE':ui.dirae(r)
    elif page in ['ELIMINADOS','ALERTAS']:ui.lists(r,page)
    elif page=='VALIDACIÓN':ui.validation(r,sources)
    elif page=='ACTUALIZAR DATOS':ui.update(r,files,version,storage,actor,role)
    elif page=='CONFIGURACIÓN':ui.configuration(r,files,version,storage,actor,role)
except (ValueError,PermissionError) as e:st.error(str(e))
except FileNotFoundError:st.error('No se encontró el paquete inicial. Siga DEPLOYMENT.md para cargar los datos.')
except Exception:st.error('No fue posible cargar o guardar los datos. Revise permisos de Google Drive, conexión y configuración. La versión válida se conserva si no se completó la actualización.')
