"""Current registrations are display-only evidence and never academic outcomes."""
import pandas as pd
from .cleaning import canonical_code, norm, names_compatible
from .semesters import ordinal
from .catalog import COLUMNS, special_eligibility

DISPLAY_COLUMNS=['Código','Código canónico','Asignatura','Tipo','Semestre','Situación','Nota',
    'Reconocimiento previo','Fuente','Observación']

def _course_matches(courses, minor, canonical):
    d=courses[(courses.minor==minor)&(courses.codigo.map(canonical_code)==canonical)&(courses.confirmado=='SI')]
    return d

def add_current_offer_rows(courses, registrations, enrollments, semester):
    """Extend confirmed course offers to this semester, only for own-Minor matches."""
    if registrations.empty:return courses.copy()
    out=courses.copy(); additions=[]; known_minors=sorted(out.loc[out.confirmado=='SI','minor'].unique())
    for r in registrations[registrations.currently_enrolled].to_dict('records'):
        for minor in known_minors:
            matches=_course_matches(out,minor,r['canonical_course_code'])
            if matches.empty:continue
            names=[x for x in matches.nombre.map(str) if norm(x) and norm(x)!=norm(r['nombre_asignatura'])]
            if names and not names_compatible([r['nombre_asignatura'],*names]):continue
            already=matches.apply(lambda x:ordinal(x.semestre_desde)<=ordinal(semester)<=ordinal(x.semestre_hasta),axis=1).any()
            if already:continue
            base=matches.iloc[0].to_dict();base['semestre_desde']=semester;base['semestre_hasta']=semester
            base['observaciones']='Oferta 2026-2 respaldada por Inscritos Electivos 2026-2; código previamente confirmado'
            additions.append(base)
    if additions:out=pd.concat([out,pd.DataFrame(additions,columns=out.columns)],ignore_index=True).drop_duplicates(['codigo','minor','semestre_desde','semestre_hasta'])
    return out

def attach_current_courses(result, registrations, semester):
    """Attach current eligible rows after academic computation; never recalculate status."""
    result=dict(result);en=result['enrollments'].copy();hist=result['history'].copy();quality=result['quality'].copy()
    if 'current_minor_courses_count' not in en:en['current_minor_courses_count']=0
    if registrations.empty:
        result.update(enrollments=en,current_enrollments=registrations)
        return result
    current_rows=[];issues=[];catalog=result['courses'];seen_current=set();conflicts_seen=set()
    known_by_code={}
    for minor,g in catalog[catalog.confirmado=='SI'].groupby('minor'):
        for c in g.codigo.map(canonical_code):known_by_code.setdefault(c,set()).add(minor)
    valid=registrations[registrations.currently_enrolled].copy()
    duplicate_mask=valid.duplicated(['matricula','canonical_course_code'],keep=False)
    for r in registrations.to_dict('records'):
        if not r['matricula']:
            issues.append(dict(nivel='ERROR',tipo='Inscripción actual sin matrícula',matricula='',detalle=f"Fila {r['source_row']}",fuente='current_enrollments',fila_origen=r['source_row']))
        if not r['currently_enrolled']:
            issues.append(dict(nivel='INFORMACIÓN',tipo='Inscripción con estado distinto de Inscrita',matricula=r['matricula'],detalle=r['enrollment_status'],fuente='current_enrollments',fila_origen=r['source_row']))
    for i,r in enumerate(valid.to_dict('records')):
        mat=r['matricula'];code=r['canonical_course_code'];partitions=en[en.matricula==mat]
        if duplicate_mask.iloc[i]:
            issues.append(dict(nivel='ADVERTENCIA',tipo='Inscripción actual duplicada',matricula=mat,detalle=f"{r['codigo']} {semester}",fuente='current_enrollments',fila_origen=r['source_row']))
        if partitions.empty:
            if code in known_by_code:
                issues.append(dict(nivel='ADVERTENCIA',tipo='Electivo actual sin participación en Minor',matricula=mat,detalle=f"{r['codigo']}: {', '.join(sorted(known_by_code[code]))}",fuente='current_enrollments',fila_origen=r['source_row']))
            continue
        for e in partitions.to_dict('records'):
            for field,label in [('nombre','Conflicto nombre actual'),('carrera','Conflicto carrera actual')]:
                left=norm(r.get(field,''));right=norm(e.get(field,''))
                mismatch=bool(left and right and (not names_compatible([left,right]) if field=='nombre' else left!=right))
                key=(e['enrollment_id'],label)
                if mismatch and key not in conflicts_seen:
                    conflicts_seen.add(key)
                    issues.append(dict(nivel='ADVERTENCIA',tipo=label,matricula=mat,detalle=f"Padrón/participación: {e.get(field,'')} / Inscripción actual: {r.get(field,'')}",fuente='current_enrollments',fila_origen=r['source_row']))
            minor=e['minor'];same=_course_matches(catalog,minor,code)
            if same.empty:
                other=known_by_code.get(code,set())-{minor}
                kind='Asignatura actual asociada a otro Minor' if other else 'Código actual no reconocido para Minor'
                detail=f"{r['codigo']} ({r['nombre_asignatura']})"+(f"; catálogo: {', '.join(sorted(other))}" if other else '')
                issues.append(dict(nivel='ADVERTENCIA',tipo=kind,matricula=mat,detalle=detail,fuente='current_enrollments',fila_origen=r['source_row']));continue
            offer=same.iloc[0].to_dict()
            offered_names=[n for n in same.nombre if norm(n) and norm(n)!=norm(r['nombre_asignatura'])]
            if offered_names and not names_compatible([r['nombre_asignatura'],*offered_names]):
                issues.append(dict(nivel='ERROR',tipo='Conflicto de nombre de asignatura actual',matricula=mat,detalle=f"{r['codigo']}: {r['nombre_asignatura']} / {' / '.join(sorted(set(offered_names)))}",fuente='current_enrollments',fila_origen=r['source_row']));continue
            eligibility=special_eligibility(e.get('carrera',''),offer) if offer['tipo']=='Electiva' and 'Emprendimiento' in minor else True
            if eligibility is not True:
                issues.append(dict(nivel='ADVERTENCIA',tipo='Elegibilidad de electiva actual pendiente/no válida',matricula=mat,detalle=f"{r['codigo']} · {minor}",fuente='current_enrollments',fila_origen=r['source_row']));continue
            dedupe_key=(e['enrollment_id'],code)
            if dedupe_key in seen_current:continue
            seen_current.add(dedupe_key)
            current_rows.append(dict(enrollment_id=e['enrollment_id'],matricula=mat,codigo=r['codigo'],canonical_course_code=code,
                nombre_asignatura=r['nombre_asignatura'],course_type=offer['tipo'],semester=semester,nota=float('nan'),outcome='',estado_final='',
                source='current_enrollments',source_row=r['source_row'],source_file='',
                unidad_academica=r['unidad_academica'],minor=minor,enrollment_status='INSCRITA',currently_enrolled=True,
                eligible_for_minor=True,counted_for_completion=False,recognized_before_enrollment=False,
                eligibility_reason='Inscrita actualmente; no afecta requisitos aprobados'))
    current=pd.DataFrame(current_rows)
    if not current.empty:
        counts=current.groupby('enrollment_id').size()
        en['current_minor_courses_count']=en.enrollment_id.map(counts).fillna(0).astype(int)
        if 'currently_enrolled' not in hist:hist['currently_enrolled']=False
        else:hist['currently_enrolled']=hist.currently_enrolled.fillna(False).astype(bool)
        if 'enrollment_status' not in hist:hist['enrollment_status']=''
        else:hist['enrollment_status']=hist.enrollment_status.fillna('')
        hist=current.copy() if hist.empty else pd.concat([hist,current],ignore_index=True,sort=False)
    if issues:quality=pd.concat([quality,pd.DataFrame(issues)],ignore_index=True)
    result.update(enrollments=en,history=hist,quality=quality,current_enrollments=registrations)
    return result

def student_history(history, enrollment_id):
    """Return the readable academic and current-registration journey."""
    h=history[history.enrollment_id==enrollment_id].copy()
    if h.empty:return pd.DataFrame(columns=DISPLAY_COLUMNS)
    rows=[]
    def flag(value):
        if pd.isna(value):return False
        return value is True or str(value).strip().lower() in {'true','1','yes'}
    for r in h.to_dict('records'):
        current=flag(r.get('currently_enrolled',False))
        outcome=str(r.get('outcome',''))
        eligible=flag(r.get('eligible_for_minor',False))
        counted=flag(r.get('counted_for_completion',False))
        if current:status='CURSANDO';recognized='No';observation='Inscrita actualmente';source=f"Inscripciones actuales {r.get('semester','')}"
        elif outcome=='FAIL':status='REPROBADA';recognized='No';observation=r.get('eligibility_reason','');source=r.get('source','')
        elif outcome=='PASS' and eligible:
            recognized='Sí' if flag(r.get('recognized_before_enrollment',False)) else 'No'
            if recognized=='Sí':status='APROBADA — RECONOCIDA PREVIA';observation='Reconocida dentro de la ventana reglamentaria previa a la inscripción'
            elif counted:status='APROBADA';observation=r.get('eligibility_reason','')
            else:status='APROBADA — ADICIONAL';observation='Asignatura válida para el Minor; adicional a las cinco seleccionadas.'
            source=r.get('source','')
        else:continue
        rows.append({'Código':r.get('codigo',''),'Código canónico':r.get('canonical_course_code',''),'Asignatura':r.get('nombre_asignatura',''),
            'Tipo':r.get('course_type',''),'Semestre':r.get('semester',''),'Situación':status,'Nota':'' if current else r.get('nota',''),
            'Reconocimiento previo':recognized,'Fuente':source,'Observación':observation,'_ordinal':ordinal(r.get('semester','')) if r.get('semester') else -1})
    out=pd.DataFrame(rows)
    if out.empty:return pd.DataFrame(columns=DISPLAY_COLUMNS)
    return out.sort_values(['_ordinal','Código canónico','Código'],kind='stable').drop(columns='_ordinal').reindex(columns=DISPLAY_COLUMNS).reset_index(drop=True)
