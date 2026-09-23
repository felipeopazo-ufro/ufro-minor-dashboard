"""Catalog evidence is semester-specific: gaps are never interpolated."""
import pandas as pd
from .cleaning import TRONCALES,norm
from .semesters import ordinal
COLUMNS=['codigo','nombre','minor','tipo','semestre_desde','semestre_hasta','unidad_academica','valida_ing_comercial','valida_contador_auditor','confirmado','observaciones','regla_especial_emprendimiento']
def build_catalog(grades,old):
    allrows=pd.concat([grades,old],ignore_index=True); rows=[]
    for (m,c,s),g in allrows.groupby(['minor','codigo','semester']):
        if not m or not c or not s:continue
        types=set(g.tipo.map(norm)); units=sorted(set(g.unidad_academica)-{''});core=c in TRONCALES[m]
        special='SI' if units and all(norm(u) in {'DIFEM','DIRECCION DE FORMACION INTEGRAL Y EMPLEABILIDAD'} for u in units) else ('NO' if units and all('DEPARTAMENTO' in norm(u) for u in units) else 'REVISAR')
        rows.append(dict(zip(COLUMNS,[c,g.iloc[0].nombre_asignatura,m,'Troncal' if core else 'Electiva',s,s,' / '.join(units),special,special,'SI' if core or types=={'ELECTIVA'} else 'NO','Evidencia: '+','.join(sorted(g.source.unique()))+'; vigencia observada, no interpolada','Sólo DIFEM para carreras restringidas'])))
    for m,codes in TRONCALES.items():
        for c in codes:
            names=allrows.loc[allrows.codigo==c,'nombre_asignatura']
            rows.append(dict(zip(COLUMNS,[c,names.iloc[0] if len(names) else c,m,'Troncal','1900-1','2200-2','','SI','SI','SI','Reglamento y regla explícita del encargo','No aplica a troncal'])))
    return pd.DataFrame(rows,columns=COLUMNS)
def index_catalog(courses):
    out={}
    for r in courses.to_dict('records'):out.setdefault((r['minor'],r['codigo']),[]).append(r)
    return out

def lookup(index,m,c,s):
    matches=[r for r in index.get((m,c),[]) if ordinal(r['semestre_desde'])<=s<=ordinal(r['semestre_hasta'])]
    if not matches:return None
    if c in TRONCALES[m]:return next((r for r in matches if r['observaciones'].startswith('Reglamento')),matches[0])
    sig={(r['tipo'],r['confirmado'],r['valida_ing_comercial'],r['valida_contador_auditor']) for r in matches}
    return matches[0] if len(sig)==1 else {'confirmado':'NO','tipo':'Electiva'}

def special_eligibility(career,course):
    """Tri-state eligibility. Unknown unit/career never silently passes."""
    n=norm(career)
    if not n:return None
    key='valida_ing_comercial' if 'INGENIERIA COMERCIAL' in n else ('valida_contador_auditor' if 'CONTADOR' in n and 'AUDITOR' in n else None)
    if not key:return True
    return {'SI':True,'NO':False}.get(norm(course.get(key,'')))
