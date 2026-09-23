"""Explicit adapters for inspected UFRO workbooks; unknown schemas are rejected."""
from io import BytesIO
import pandas as pd
from .cleaning import text,matricula,minor,code,norm
from .semesters import normalize
SCHEMAS={
'inscritos': ('Hoja1',0,{'Matrícula':'matricula','Nombre histórico':'nombre','Programa':'minor','Inscripción histórico':'semester_enrolled'}),
'calificaciones':('Calificaciones Minor',0,{'Matrícula':'matricula','Nombre':'nombre','Carrera/Programa':'carrera','Año':'year','Sem.':'term','Código':'codigo','Nombre Asignatura':'nombre_asignatura','Nota':'nota','Estado Final':'estado_final','Unidad':'unidad_academica','Programa Minor':'minor','Tipo Asignatura':'tipo'}),
'master':('Sheet1',1,{'Matrícula':'matricula','Nombre':'nombre','Nombre Carrera':'carrera'}),
'seguimiento':('Base completa Minors',0,{'Matrícula':'matricula','Nombre':'nombre','Carrera/Programa':'carrera','Año asignatura':'year','Semestre asignatura':'term','Código_asig':'codigo','Nombre Asignatura':'nombre_asignatura','Nota':'nota','Estado Final':'estado_final','Unidad':'unidad_academica','Programa Minor':'minor','Tipo Asignatura':'tipo','Año inscripción Minor':'enroll_year','Semestre inscripción Minor':'enroll_term','Estado minor calc':'old_status','Año egreso Minor':'grad_year','Semestre egreso Minor':'grad_term'})}
def safe_sem(v):
    try:return normalize(v)
    except (ValueError,TypeError):return ''
def pair(y,s):
    try:return safe_sem(f'{int(float(y))}-{int(float(s))}')
    except (ValueError,TypeError):return ''
def load_source(kind, data):
    sn,header,mapping=SCHEMAS[kind]
    try:
        book=pd.ExcelFile(BytesIO(data))
        if sn not in book.sheet_names:
            if len(book.sheet_names)==1:sn=book.sheet_names[0]
            else:raise ValueError(f'Falta la hoja {sn}.')
        df=pd.read_excel(book,sheet_name=sn,header=header,dtype=object).dropna(how='all')
    except ValueError:raise
    except Exception as e:raise ValueError('No se pudo leer el archivo Excel.') from e
    missing=set(mapping)-set(df.columns)
    if missing:raise ValueError('El archivo no contiene las columnas requeridas: '+', '.join(sorted(missing)))
    df=df.rename(columns=mapping).copy(); df['source_row']=df.index+header+2; df['source']=kind
    df['matricula_original']=df.matricula.map(text); df['matricula']=df.matricula.map(matricula)
    for c in ['nombre','carrera','nombre_asignatura','unidad_academica','estado_final','tipo']:
        if c in df:df[c]=df[c].map(text)
    if 'minor' in df:df['minor']=df.minor.map(minor)
    if 'codigo' in df:df['codigo']=df.codigo.map(code)
    if 'year' in df:df['semester']=df.apply(lambda r:pair(r.year,r.term),axis=1)
    if 'semester_enrolled' in df:df['semester_original']=df.semester_enrolled.map(text);df['semester_enrolled']=df.semester_enrolled.map(safe_sem)
    if 'enroll_year' in df:df['semester_enrolled']=df.apply(lambda r:pair(r.enroll_year,r.enroll_term),axis=1)
    if 'grad_year' in df:df['graduation_semester']=df.apply(lambda r:pair(r.grad_year,r.grad_term),axis=1)
    if 'nota' in df:
        df['nota_original']=df.nota.map(text)
        df['nota']=pd.to_numeric(df.nota.map(lambda x:text(x).replace(',','.')),errors='coerce')
        df['outcome']=df.estado_final.map(lambda x:{'APROBADA':'PASS','REPROBADA':'FAIL'}.get(norm(x),'UNKNOWN'))
    return df

def validate_upload(kind,data):
    d=load_source(kind,data)
    if d.empty:raise ValueError('El archivo no contiene registros.')
    if (d.matricula=='').any():raise ValueError('Hay matrículas vacías.')
    for c in ['minor','semester','semester_enrolled','codigo']:
        if c in d and (d[c]=='').any():raise ValueError(f'Hay valores vacíos o inválidos en {c}.')
    if 'nota' in d and (d.nota.isna()|~d.nota.between(1,7)).any():raise ValueError('Hay notas fuera de la escala 1–7 o no numéricas.')
    return d
