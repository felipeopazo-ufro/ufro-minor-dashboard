"""Create initial private snapshot from the four workbooks, without committing them."""
import argparse,json
from pathlib import Path
from src.storage import FILES,pack
from src.data_loader import load_source
from src.catalog import build_catalog
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',default='data/private/minor_snapshot.zip');args=p.parse_args()
root=Path(args.input);patterns={'inscritos':'Inscritos*.xlsx','calificaciones':'Calificaciones*.xlsx','master':'Excel_Master*.xlsx','seguimiento':'Minor seguimiento*.xlsx'}
files={}
for k,pattern in patterns.items():
    matches=list(root.glob(pattern))
    if len(matches)!=1:raise ValueError(f'Se requiere un único archivo {pattern}.')
    files[FILES[k]]=matches[0].read_bytes()
sources={k:load_source(k,files[n]) for k,n in FILES.items()}
files['minor_courses.csv']=build_catalog(sources['calificaciones'],sources['seguimiento']).to_csv(index=False).encode()
files['exceptions.csv']=Path('config/exceptions_template.csv').read_bytes();files['settings.json']=json.dumps({'current_semester':'2026-2'}).encode();files['audit.json']=b'[]'
official=list(root.glob('Avances Minor Ingl*.xls*'))
if len(official)==1:
    from src.official import load_official,OFFICIAL_FILE
    load_official(official[0].read_bytes());files[OFFICIAL_FILE]=official[0].read_bytes()
elif len(official)>1:raise ValueError('Deje sólo una versión del avance oficial de Inglés en la carpeta de entrada.')
out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(pack(files));print('Paquete inicial creado.')
