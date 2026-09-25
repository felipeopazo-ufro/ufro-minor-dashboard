"""AppTest: authentication gate plus real-data pages when local fixture is supplied."""
import os
from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_closed_without_credentials():
 app=AppTest.from_file(Path('app.py').resolve(),default_timeout=60).run()
 assert not app.exception
 assert len(app.dataframe)==0
 assert not app.sidebar.radio

def test_local_pages(monkeypatch):
 if not Path('data/private/minor_snapshot.zip').exists():return
 monkeypatch.setenv('MINOR_LOCAL_DEVELOPMENT','1')
 app=AppTest.from_file(Path('app.py').resolve(),default_timeout=90)
 app.secrets={'app':{'development_mode':True},'storage':{'mode':'LOCAL','local_path':'data/private/minor_snapshot.zip'}}
 app.run();assert not app.exception;assert not app.error
 probable=next((w for w in app.selectbox if w.label=='Probable excepcionalidad'),None)
 assert probable is not None
 probable.set_value('Sí').run();assert not app.exception;assert not app.error
 probable.set_value('Todas').run();assert not app.exception;assert not app.error
 from src.storage import unpack
 if 'avance_oficial_ingles.xlsx' in unpack(Path('data/private/minor_snapshot.zip').read_bytes()):
  assert any('351 completados' in item.value for item in app.info)
 for page in ['BUSCAR ESTUDIANTE','VISTA DIRAE','ELIMINADOS','ALERTAS','VALIDACIÓN','ACTUALIZAR DATOS','CONFIGURACIÓN','PANORAMA']:
  app.sidebar.radio[0].set_value(page).run();assert not app.exception;assert not app.error
  if page=='BUSCAR ESTUDIANTE':
   app.text_input[0].set_value('a').run();assert not app.exception;assert not app.error
