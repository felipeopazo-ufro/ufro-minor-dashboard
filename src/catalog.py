"""Catalog evidence is semester-specific: gaps are never interpolated."""
import pandas as pd
from .cleaning import TRONCALES,norm,canonical_code,HISTORICAL_EQUIVALENCES
from .semesters import ordinal
COLUMNS=['codigo','nombre','minor','tipo','semestre_desde','semestre_hasta','unidad_academica','valida_ing_comercial','valida_contador_auditor','confirmado','observaciones','regla_especial_emprendimiento']
def build_catalog(grades,old):
    allrows=pd.concat([grades,old],ignore_index=True); rows=[]
    for (m,c,s),g in allrows.groupby(['minor','codigo','semester']):
        if not m or not c or not s:continue
        types=set(g.tipo.map(norm)); units=sorted(set(g.unidad_academica)-{''});core=canonical_code(c) in TRONCALES[m]
        special=unit_eligibility(' / '.join(units))
        rows.append(dict(zip(COLUMNS,[c,g.iloc[0].nombre_asignatura,m,'Troncal' if core else 'Electiva',s,s,' / '.join(units),special,special,'SI' if core or types=={'ELECTIVA'} else 'NO','Evidencia: '+','.join(sorted(g.source.unique()))+'; vigencia observada, no interpolada','Sólo DIFEM para carreras restringidas'])))
    for m,codes in TRONCALES.items():
        for c in codes:
            names=allrows.loc[allrows.codigo==c,'nombre_asignatura']
            rows.append(dict(zip(COLUMNS,[c,names.iloc[0] if len(names) else c,m,'Troncal','1900-1','2200-2','','SI','SI','SI','Reglamento y regla explícita del encargo','No aplica a troncal'])))
    return pd.DataFrame(rows,columns=COLUMNS)
def unit_eligibility(unit):
    """Formación General's own offerings qualify for the restricted careers."""
    units=[norm(x) for x in unit.split(' / ') if x.strip()]
    if units and all(u in {'DIFEM','DIRECCION DE FORMACION INTEGRAL Y EMPLEABILIDAD'} or
                     'FORMACION GENERAL' in u for u in units):return 'SI'
    if units and all('DEPARTAMENTO' in u for u in units):return 'NO'
    return 'REVISAR'

def equivalence_conflicts(*sources):
    """Hold a same-number equivalence when observed CIP and DFI names differ."""
    names={}
    for data in sources:
        for r in data.to_dict('records'):
            c=r.get('codigo','');name=norm(r.get('nombre_asignatura',''))
            if not name or name==c or not (c in HISTORICAL_EQUIVALENCES or c in HISTORICAL_EQUIVALENCES.values()):continue
            names.setdefault((r.get('minor',''),c),set()).add(name)
    blocked={}; details=[]
    for (m,c),original in names.items():
        later=names.get((m,HISTORICAL_EQUIVALENCES.get(c,'')))
        if c in HISTORICAL_EQUIVALENCES and later and original!=later:
            blocked.setdefault(m,set()).add(c)
            details.append((m,c,HISTORICAL_EQUIVALENCES[c],sorted(original),sorted(later)))
    return blocked,details

def index_catalog(courses,blocked=()):
    out={}
    for r in courses.to_dict('records'):
        canonical=canonical_code(r['codigo'],blocked.get(r['minor'],()) if isinstance(blocked,dict) else blocked)
        out.setdefault((r['minor'],canonical),[]).append(r)
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
