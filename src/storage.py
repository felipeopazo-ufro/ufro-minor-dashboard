"""One versioned ZIP snapshot prevents partial updates across source files."""
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED
from pathlib import Path
import hashlib,json,os,threading
LOCK=threading.RLock()
FILES={'inscritos':'inscritos.xlsx','calificaciones':'calificaciones.xlsx','master':'master.xlsx','seguimiento':'seguimiento.xlsx'}
CIP_FILE='cip_historico.xlsx'
CURRENT_ENROLLMENTS_FILE='current_enrollments.xls'

def pack(files):
    b=BytesIO()
    with ZipFile(b,'w',ZIP_DEFLATED) as z:
        for n,v in files.items():z.writestr(n,v)
    return b.getvalue()
def unpack(data):
    with ZipFile(BytesIO(data)) as z:
        if sum(f.file_size for f in z.infolist())>250_000_000:raise ValueError('Paquete demasiado grande.')
        return {n:z.read(n) for n in z.namelist()}
def digest(data):return hashlib.sha256(data).hexdigest()
class LocalStorage:
    def __init__(self,path):self.path=Path(path)
    def version(self):
        return digest(self.path.read_bytes()) if self.path.exists() else digest(b'')
    def read(self):
        b=self.path.read_bytes();return unpack(b),digest(b)
    def write(self,files,expected):
        with LOCK:
            current=self.path.read_bytes() if self.path.exists() else b''
            if digest(current)!=expected:raise ValueError('Los datos cambiaron. Recargue antes de guardar.')
            b=pack(files);self.path.parent.mkdir(parents=True,exist_ok=True)
            if current:
                backup=self.path.parent/'backups';backup.mkdir(exist_ok=True);(backup/(digest(current)+'.zip')).write_bytes(current)
            temp=self.path.with_suffix('.tmp');temp.write_bytes(b);os.replace(temp,self.path)
            return digest(b)
def make_storage(settings):
    mode=settings.get('storage',{}).get('mode','GOOGLE_DRIVE')
    if mode=='LOCAL':return LocalStorage(settings['storage'].get('local_path','data/private/minor_snapshot.zip'))
    if mode=='GOOGLE_DRIVE':
        from integrations.google_drive import DriveStorage
        return DriveStorage(settings['google_service_account'],settings['storage']['snapshot_file_id'])
    raise ValueError('Modo de almacenamiento desconocido.')
