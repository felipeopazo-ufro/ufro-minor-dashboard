from io import BytesIO
import pandas as pd
from .catalog import COLUMNS
from .cleaning import MINORS,TRONCALES,norm,canonical_code,HISTORICAL_EQUIVALENCES
from .catalog import unit_eligibility
from .semesters import ordinal
EXCEPTION_COLUMNS=['matricula','minor','enrollment_id','semestre_afectado','tipo_excepcion','observacion','contabiliza_en_plazo','aprobada']
def read_csv(data):return pd.read_csv(BytesIO(data),dtype=str,keep_default_na=False)
def validate_courses(data):
    d=read_csv(data)
    if set(COLUMNS)-set(d):raise ValueError('Faltan columnas del catálogo.')
    # Read older snapshots safely; their historic CIP rows were labeled electivas.
    legacy=d.codigo.isin(HISTORICAL_EQUIVALENCES)
    core=d.apply(lambda r:canonical_code(r['codigo']) in TRONCALES.get(r['minor'],()),axis=1)
    d.loc[legacy & core,'tipo']='Troncal';d.loc[legacy & core,'confirmado']='SI'
    restricted=d.minor=='Minor en Emprendimiento'
    for i in d.index[restricted]:
        flag=unit_eligibility(d.at[i,'unidad_academica'])
        if flag!='REVISAR':
            for career_flag in ('valida_ing_comercial','valida_contador_auditor'):
                if d.at[i,career_flag]=='REVISAR':d.at[i,career_flag]=flag
    for r in d.to_dict('records'):
        if not r['codigo'] or r['minor'] not in MINORS or r['tipo'] not in ['Troncal','Electiva']:raise ValueError('Código, Minor o tipo inválido.')
        if ordinal(r['semestre_desde'])>ordinal(r['semestre_hasta']):raise ValueError('Rango de vigencia invertido.')
        if (canonical_code(r['codigo']) in TRONCALES[r['minor']]) != (r['tipo']=='Troncal'):raise ValueError('Clasificación incompatible con troncales obligatorias.')
        for f in ['valida_ing_comercial','valida_contador_auditor']:
            if r[f] not in ['SI','NO','REVISAR']:raise ValueError(f'{f}: use SI, NO o REVISAR.')
        if r['confirmado'] not in ['SI','NO']:raise ValueError('confirmado debe ser SI o NO.')
    return d

def validate_exceptions(data,enrollments):
    d=read_csv(data)
    if set(EXCEPTION_COLUMNS)-set(d):raise ValueError('Faltan columnas de excepciones.')
    for r in d.to_dict('records'):
        ordinal(r['semestre_afectado'])
        matches=enrollments[(enrollments.matricula==r['matricula'])&(enrollments.minor==r['minor'])]
        if r['enrollment_id']:matches=matches[matches.enrollment_id==r['enrollment_id']]
        if len(matches)!=1:raise ValueError('Excepción sin participación única. Complete enrollment_id.')
        if r['tipo_excepcion'] not in ['Movilidad','Postergación','Retiro temporal','Prórroga extraordinaria']:raise ValueError('Tipo de excepción no reconocido.')
        if r['tipo_excepcion']=='Prórroga extraordinaria':
            try:
                v=str(r.get('semestres_extension','')).strip();n=int(v)
                if n<1 or str(n)!=v:raise ValueError()
            except (ValueError,TypeError):raise ValueError('La prórroga requiere semestres_extension entero positivo.')
        if not r['observacion']:raise ValueError('Documente el respaldo de cada excepción en observacion.')
        if norm(r['contabiliza_en_plazo']) not in ['SI','NO'] or norm(r['aprobada']) not in ['SI','NO']:raise ValueError('Use SI o NO en aprobación y cómputo.')
    return d
