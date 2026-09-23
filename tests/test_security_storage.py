import pytest,pandas as pd
from io import BytesIO
from src.auth import role_for,require_admin
from src.storage import LocalStorage,digest,pack,unpack
from src.excel import excel_bytes
from src.configuration import validate_courses
from openpyxl import load_workbook

def test_auth():
 allow={'a@ufrontera.cl':'ADMIN'}
 assert role_for({'email':'a@ufrontera.cl','email_verified':True},allow)=='ADMIN'
 for u in [{'email':'a@ufrontera.cl','email_verified':False},{'email':'b@ufrontera.cl','email_verified':True},{'email':'a@ufrontera.cl.evil','email_verified':True},{}]:assert role_for(u,allow) is None

def test_role():
 with pytest.raises(PermissionError):require_admin('CONSULTA')
def test_atomic_storage(tmp_path):
 s=LocalStorage(tmp_path/'snapshot.zip');v=s.write({'a':b'1'},digest(b''));f,v=s.read();assert f=={'a':b'1'}
 s.write({'a':b'2'},v)
 with pytest.raises(ValueError):s.write({'a':b'3'},v)
 assert s.read()[0]['a']==b'2' and len(list((tmp_path/'backups').glob('*.zip')))==1

def test_export_roundtrip():
 b=excel_bytes({'DIRAE':pd.DataFrame({'Matrícula':['00123456789'],'Nota':[5.6],'Nombre':['=HYPERLINK("evil")']})})
 w=load_workbook(BytesIO(b));s=w.active
 assert s['A2'].value=='00123456789' and s['A2'].data_type=='s';assert s['B2'].value==5.6;assert s['C2'].data_type=='s';assert s.freeze_panes=='A2' and s.auto_filter.ref=='A1:C2'

def test_missing_headers_rejected():
 from src.data_loader import validate_upload
 b=excel_bytes({'Hoja1':pd.DataFrame({'Otro':['dato']})})
 with pytest.raises(ValueError,match='columnas requeridas'):validate_upload('inscritos',b)

def test_no_data_is_not_authorized():
 assert role_for({'email':'a@ufrontera.cl','email_verified':True},{'a@ufrontera.cl':'OWNER'}) is None
