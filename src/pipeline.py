import pandas as pd
from .cleaning import norm,names_compatible
from .catalog import build_catalog,index_catalog,equivalence_conflicts
from .status_engine import calculate_minor_status

def process(sources,current='2026-2',courses=None,exceptions=None,blocked_equivalences=None):
    en=sources['inscritos'];old=sources['seguimiento'];master=sources['master'];issues=[]
    gr=pd.concat([sources['calificaciones'],sources['cip_historico']],ignore_index=True) if 'cip_historico' in sources else sources['calificaciones']
    def issue(level,kind,mat='',detail='',source='',row=''):
        issues.append(dict(nivel=level,tipo=kind,matricula=mat,detalle=str(detail),fuente=source,fila_origen=row))
    for kind,d in sources.items():
        for field in ['matricula','minor','codigo','semester','semester_enrolled']:
            if field not in d:continue
            for r in d[d[field]==''].to_dict('records'):
                if kind=='seguimiento' and field=='semester_enrolled' and norm(r.get('enroll_year'))=='NO INSCRITO':
                    issue('INFORMACIÓN','Histórico sin inscripción',r['matricula'],'Fuente declara No inscrito',kind,r['source_row'])
                else:issue('ERROR','Campo inválido',r['matricula'],field,kind,r['source_row'])
        if 'nota' in d:
            for r in d[d.nota.isna()|~d.nota.between(1,7)|(d.outcome=='UNKNOWN')].to_dict('records'):issue('ERROR','Nota/estado inválido',r['matricula'],r['nota_original'],kind,r['source_row'])
        cmp=[c for c in d if c not in ['source_row','source','matricula_original']]
        for r in d[d.duplicated(cmp)].to_dict('records'):issue('INFORMACIÓN','Duplicado técnico',r['matricula'],'Conservado en fuente; no duplica requisitos',kind,r['source_row'])
    if courses is None:courses=build_catalog(sources['calificaciones'],old)
    blocked,conflicts=equivalence_conflicts(gr,old)
    for m,codes in (blocked_equivalences or {}).items():blocked.setdefault(m,set()).update(codes)
    cat=index_catalog(courses,blocked)
    for m,c,later,left,right in conflicts:issue('ERROR','Equivalencia histórica ambigua','',f'{m}: {c} / {later}: {left} / {right}')
    banks={k:{mat:g for mat,g in d.groupby('matricula')} for k,d in sources.items()}
    grades={mat:g.to_dict('records') for mat,g in gr.groupby('matricula')}
    enrollments=[];histories=[]
    exact=en.drop_duplicates(['matricula','minor','semester_enrolled'])
    repeated=set(tuple(x) for x in exact.loc[exact.duplicated(['matricula','minor'],keep=False),['matricula','minor']].values)
    for r in exact.to_dict('records'):
        mat=r['matricula'];review=[];e={k:r[k] for k in ['matricula','nombre','minor','semester_enrolled']};e['enrollment_id']='|'.join([mat,r['minor'],r['semester_enrolled']]); e['carrera']=''
        if (mat,r['minor']) in repeated:review.append('Reinscripción en el mismo Minor: confirmar continuidad/eliminación previa')
        for field in ['nombre','carrera']:
            candidates=[]
            for k in ['master','seguimiento','calificaciones','inscritos']:
                d=banks[k].get(mat)
                if d is None or field not in d:continue
                d=d.sort_values('semester',ascending=False) if 'semester' in d else d
                candidates.extend((x,k) for x in d[field].unique() if x)
            if candidates:e[field]=candidates[0][0];e[field+'_fuente']=candidates[0][1]
            variants={norm(v) for v,k in candidates}
            conflict=not names_compatible([v for v,k in candidates]) if field=='nombre' else len(variants)>1
            if conflict:
                issue('ADVERTENCIA','Conflicto '+field,mat,' / '.join(sorted(set(v for v,k in candidates))))
                if field=='nombre':review.append('Nombres incompatibles entre fuentes')
                if field=='carrera' and 'Emprendimiento' in e['minor']:
                    restricted={('INGENIERIA COMERCIAL' in v or ('CONTADOR' in v and 'AUDITOR' in v)) for v in variants}
                    if len(restricted)>1:review.append('Conflicto de carrera afecta restricción de Emprendimiento')
            if not e[field]:issue('ADVERTENCIA','Sin '+field,mat);review.append('Sin '+field)
        if mat not in grades:issue('INFORMACIÓN','Inscrito sin calificaciones',mat,'Puede ser nuevo ingreso')
        e['review_reasons']=review
        result=calculate_minor_status(e,grades.get(mat,[]),cat,exceptions or [],current,blocked.get(e['minor'],()))
        histories.extend(result.pop('history'));enrollments.append(result)
        if result['requires_review']:issue('ERROR','Participación requiere revisión',mat,result['status_reason'])
    for mat in set(old.matricula)-set(en.matricula):issue('ADVERTENCIA','Sólo seguimiento',mat,'No se incorporó al universo inscrito')
    for r in courses[courses.confirmado!='SI'].to_dict('records'):issue('ADVERTENCIA','Catálogo pendiente','',r['codigo']+' '+r['minor']+' '+r['semestre_desde'])
    return {'enrollments':pd.DataFrame(enrollments),'history':pd.DataFrame(histories),'quality':pd.DataFrame(issues,columns=['nivel','tipo','matricula','detalle','fuente','fila_origen']),'courses':courses,'current':current}
