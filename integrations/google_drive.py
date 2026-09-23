"""Read/update an existing restricted Drive file. Does not create owned SA files."""
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload,MediaIoBaseUpload
from src.storage import unpack,pack,LOCK
class DriveStorage:
    def __init__(self,info,file_id):
        credentials=service_account.Credentials.from_service_account_info(dict(info),scopes=['https://www.googleapis.com/auth/drive'])
        self.api=build('drive','v3',credentials=credentials,cache_discovery=False);self.file_id=file_id
    def version(self):
        return str(self.api.files().get(fileId=self.file_id,fields='version',supportsAllDrives=True).execute()['version'])
    def read(self):
        before=self.version();b=BytesIO();down=MediaIoBaseDownload(b,self.api.files().get_media(fileId=self.file_id,supportsAllDrives=True));done=False
        while not done:_,done=down.next_chunk()
        if self.version()!=before:raise ValueError('Los datos cambiaron durante la lectura. Recargue.')
        return unpack(b.getvalue()),before
    def write(self,files,expected):
        # Single application writer. Out-of-app concurrent edits are unsupported.
        with LOCK:
            if self.version()!=expected:raise ValueError('Otra actualización modificó los datos. Recargue.')
            media=MediaIoBaseUpload(BytesIO(pack(files)),mimetype='application/zip',resumable=False)
            r=self.api.files().update(fileId=self.file_id,media_body=media,keepRevisionForever=True,supportsAllDrives=True,fields='version').execute()
            return str(r['version'])
