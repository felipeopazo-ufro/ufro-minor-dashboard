from pathlib import Path
import streamlit as st
from src.auth import authenticate,PAGES
from src.storage import make_storage
from src.runtime_cache import (
    CALCULATION_CACHE_SCHEMA,
    clear_snapshot_calculation_cache,
    load_snapshot_calculation,
    snapshot_cache_key,
)
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
    if st.sidebar.button('Recargar datos'):
        clear_snapshot_calculation_cache()
        st.session_state.pop('_loaded_snapshot_cache_key',None)
        st.rerun()
    storage_config=settings.get('storage',{})
    mode=storage_config.get('mode','GOOGLE_DRIVE')
    snapshot_file_id=storage_config.get('snapshot_file_id','')
    local_path=storage_config.get('local_path','data/private/minor_snapshot.zip') if mode=='LOCAL' else ''
    snapshot_version=storage.version()
    cache_key=snapshot_cache_key(mode,snapshot_file_id,snapshot_version,local_path)
    is_new_for_session=st.session_state.get('_loaded_snapshot_cache_key')!=cache_key
    if is_new_for_session:
        with st.spinner('Cargando fuentes y calculando trayectorias…'):
            files,version,r,sources=load_snapshot_calculation(
                mode,
                snapshot_file_id,
                snapshot_version,
                local_path,
                CALCULATION_CACHE_SCHEMA,
                _google_service_account=settings.get('google_service_account'),
            )
        st.session_state['_loaded_snapshot_cache_key']=cache_key
    else:
        files,version,r,sources=load_snapshot_calculation(
            mode,
            snapshot_file_id,
            snapshot_version,
            local_path,
            CALCULATION_CACHE_SCHEMA,
            _google_service_account=settings.get('google_service_account'),
        )
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
