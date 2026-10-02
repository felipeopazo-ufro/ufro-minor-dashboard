"""Explicit adapters for inspected UFRO workbooks; unknown schemas are rejected."""
from io import BytesIO
import pandas as pd
from .cleaning import text,matricula,minor,code,norm,canonical_code,MINORS
from .semesters import normalize
import re
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
    if kind=='master':
        optional={'Estado Académico':'estado_academico','Estado Alumno':'estado_alumno','Año':'master_year','Sem.':'master_term'}
        for original,target in optional.items():
            if original in df:df[target]=df[original].map(text)
    df['matricula_original']=df.matricula.map(text); df['matricula']=df.matricula.map(matricula)
    for c in ['nombre','carrera','nombre_asignatura','unidad_academica','estado_final','tipo']:
        if c in df:df[c]=df[c].map(text)
    if 'minor' in df:df['minor']=df.minor.map(minor)
    if 'codigo' in df:df['codigo']=df.codigo.map(code)
    if 'codigo' in df:df['canonical_course_code']=df.codigo.map(canonical_code)
    if 'year' in df:df['semester']=df.apply(lambda r:pair(r.year,r.term),axis=1)
    if 'semester_enrolled' in df:df['semester_original']=df.semester_enrolled.map(text);df['semester_enrolled']=df.semester_enrolled.map(safe_sem)
    if 'enroll_year' in df:df['semester_enrolled']=df.apply(lambda r:pair(r.enroll_year,r.enroll_term),axis=1)
    if 'grad_year' in df:df['graduation_semester']=df.apply(lambda r:pair(r.grad_year,r.grad_term),axis=1)
    if 'nota' in df:
        df['nota_original']=df.nota.map(text)
        df['nota']=pd.to_numeric(df.nota.map(lambda x:text(x).replace(',','.')),errors='coerce')
        df['outcome']=df.estado_final.map(lambda x:{'APROBADA':'PASS','REPROBADA':'FAIL'}.get(norm(x),'UNKNOWN'))
    return df

def load_current_enrollments(data,semester='2026-2'):
    """Read the semester's registration roster as non-grade evidence only."""
    try:
        book=pd.ExcelFile(BytesIO(data))
        d=pd.read_excel(book,sheet_name=book.sheet_names[0],dtype=object).dropna(how='all')
    except Exception as exc:raise ValueError('No se pudo leer el archivo de inscripciones actuales.') from exc
    aliases={'Unidad':'unidad_academica','Código':'codigo','Nombre Asignatura':'nombre_asignatura',
        'Matrícula':'matricula','Nombre':'nombre','Estado Inscr.':'enrollment_status',
        'Carrera/Programa':'carrera','Código.1':'codigo_carrera','E-Mail':'email'}
    missing=set(aliases)-set(d.columns)
    if missing:raise ValueError('El archivo de inscripciones actuales no contiene: '+', '.join(sorted(missing)))
    d=d.rename(columns=aliases).copy();d['source_row']=d.index+2;d['source']='current_enrollments'
    from .cleaning import text,code,canonical_code,matricula,norm
    for field in ['unidad_academica','nombre_asignatura','nombre','enrollment_status','carrera','email','codigo_carrera']:
        d[field]=d[field].map(text)
    d['matricula_original']=d.matricula.map(text);d['matricula']=d.matricula.map(matricula)
    d['codigo_original']=d.codigo.map(text);d['codigo']=d.codigo.map(code);d['canonical_course_code']=d.codigo.map(canonical_code)
    d['semester']=semester;d['currently_enrolled']=d.enrollment_status.map(lambda x:norm(x)=='INSCRITA')
    d['nota']=pd.NA;d['outcome']='';d['estado_final']=''
    return d

def load_cip(data):
    """The historic CIP sheet's Código is a career ID; Source.Name has course/term."""
    try:d=pd.read_excel(BytesIO(data),sheet_name='Asignaturas CIP',dtype=object).dropna(how='all')
    except Exception as exc:raise ValueError('No se pudo leer la fuente histórica CIP.') from exc
    required={'Source.Name','Matricula','Nombre_alumno','Nota','Situación'}
    if required-set(d):raise ValueError('Faltan columnas en la fuente CIP.')
    rows=[]
    for i,r in d.iterrows():
        match=re.fullmatch(r'(CIP(?:165|183|185))\s+(\d{4})-([12])\.xls[x]?',text(r['Source.Name']),re.I)
        if not match:raise ValueError(f'Nombre de archivo CIP no reconocido en fila {i+2}.')
        c=code(match[1]);s=normalize(f'{match[2]}-{match[3]}')
        n=pd.to_numeric(text(r['Nota']).replace(',','.'),errors='coerce')
        state=text(r['Situación']);outcome={'APROBADA':'PASS','REPROBADA':'FAIL'}.get(norm(state),'UNKNOWN')
        if pd.isna(n) or not 1<=n<=7 or outcome=='UNKNOWN':raise ValueError(f'Nota o situación CIP inválida en fila {i+2}.')
        rows.append(dict(matricula=matricula(r['Matricula']),matricula_original=text(r['Matricula']),
            nombre=text(r['Nombre_alumno']),carrera=text(r.get('Carrera / Programa')),
            codigo=c,canonical_course_code=canonical_code(c),semester=s,nota=float(n),
            nota_original=text(r['Nota']),estado_final=state,outcome=outcome,
            nombre_asignatura=c,unidad_academica='',tipo='Troncal',
            minor=MINORS[1] if c=='CIP165' else MINORS[0],
            source='cip_historico',source_file=text(r['Source.Name']),source_row=i+2))
    return pd.DataFrame(rows)

def validate_upload(kind,data):
    d=load_source(kind,data)
    if d.empty:raise ValueError('El archivo no contiene registros.')
    if (d.matricula=='').any():raise ValueError('Hay matrículas vacías.')
    for c in ['minor','semester','semester_enrolled','codigo']:
        if c in d and (d[c]=='').any():raise ValueError(f'Hay valores vacíos o inválidos en {c}.')
    if 'nota' in d and (d.nota.isna()|~d.nota.between(1,7)).any():raise ValueError('Hay notas fuera de la escala 1–7 o no numéricas.')
    return d
