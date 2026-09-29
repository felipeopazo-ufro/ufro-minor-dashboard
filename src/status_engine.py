"""Pure auditable academic engine. No UI or storage dependencies."""
import pandas as pd
from .semesters import ordinal,semester
from .cleaning import TRONCALES,norm,canonical_code
from .catalog import lookup,special_eligibility,index_catalog

def calculate_minor_status(enrollment,grades,courses,exceptions,current_semester,blocked_equivalences=()):
    e=enrollment; m=e['minor']; reviews=list(e.get('review_reasons',[])); history=[]
    base=dict(e); base.pop('review_reasons',None)
    base.update(deadline_semester='',ordinary_deadline_semester='',completion_semester='',graduation_semester='',semesters_over_deadline=0,probable_exceptionality=False,exception_type='',troncales_required=2,electives_required=3,troncales_completed=0,electives_completed=0,total_completed=0,pending_troncales='',pending_electives=3,total_pending=5,alert_level='',exception_count=0,completed_out_of_time=False,causal_semester='')
    try:start=ordinal(e['semester_enrolled']); now=ordinal(current_semester)
    except ValueError:
        return dict(base,status='REQUIERE REVISIÓN',status_reason='Inscripción con semestre inválido',requires_review=True,history=[])
    if m not in TRONCALES:return dict(base,status='REQUIERE REVISIÓN',status_reason='Minor desconocido',requires_review=True,history=[])
    cat=index_catalog(courses,blocked_equivalences) if isinstance(courses,pd.DataFrame) else courses
    excluded=set();extensions={};documented_types=set()
    for x in exceptions:
        if x.get('matricula')!=e['matricula'] or x.get('minor')!=m:continue
        if x.get('enrollment_id') and x['enrollment_id']!=e['enrollment_id']:continue
        extra=norm(x.get('tipo_excepcion'))=='PRORROGA EXTRAORDINARIA'
        if not extra and norm(x.get('contabiliza_en_plazo')) not in {'NO','FALSE'}:continue
        try:s=ordinal(x['semestre_afectado'])
        except (KeyError,ValueError):reviews.append('Excepción con semestre inválido');continue
        if norm(x.get('aprobada'))!='SI':reviews.append('Excepción pendiente de aprobación');continue
        if extra:
            try:
                n=int(x.get('semestres_extension',''))
                if n<1 or not str(x.get('observacion','')).strip():raise ValueError()
                extensions[(s,str(x.get('observacion','')))]=n
                documented_types.add(str(x.get('tipo_excepcion','')).strip())
            except (ValueError,TypeError):reviews.append('Prórroga extraordinaria sin extensión o respaldo válido')
        elif s>=start:
            excluded.add(s);documented_types.add(str(x.get('tipo_excepcion','')).strip())
    extra_count=sum(extensions.values())
    ordinary_end=start+5
    end=ordinary_end+extra_count
    while True:
        new=start+5+extra_count+sum(start<=s<=end for s in excluded)
        if new==end:break
        end=new
    relevant=[dict(r) for r in grades if r.get('matricula')==e['matricula']]
    groups={}
    for r in relevant:
        c=canonical_code(r.get('codigo',''),blocked_equivalences); raw=r.get('semester','')
        if not raw:
            if r.get('minor')==m:reviews.append('Calificación con semestre inválido')
            continue
        s=ordinal(raw)
        if r.get('minor')!=m and (m,c) not in cat:continue
        groups.setdefault((c,s),[]).append(r)
    valid=[]; failures=[]
    for (c,s),attempts in sorted(groups.items(),key=lambda kv:(kv[0][1],kv[0][0])):
        signatures={(str(r.get('nota')),r.get('outcome')) for r in attempts}
        ambiguous=len(signatures)>1
        r=next((a for a in attempts if a.get('source')=='calificaciones'),attempts[0]);course=lookup(cat,m,c,s); core=c in TRONCALES[m]
        h={k:r.get(k,'') for k in ['codigo','nombre_asignatura','semester','nota','estado_final','outcome','source_row','source_file','unidad_academica','source']}
        h['canonical_course_code']=c
        observed=next((x for x in cat.get((m,c),[]) if x['codigo']==r.get('codigo') and
            ordinal(x['semestre_desde'])<=s<=ordinal(x['semestre_hasta']) and x.get('unidad_academica')),None)
        if not h['unidad_academica'] and observed:h['unidad_academica']=observed['unidad_academica']
        if h['nombre_asignatura']==r.get('codigo') and observed:h['nombre_asignatura']=observed.get('nombre',h['nombre_asignatura'])
        if h['nombre_asignatura']==r.get('codigo') and course:h['nombre_asignatura']=course.get('nombre',h['nombre_asignatura'])
        h.update(enrollment_id=e['enrollment_id'],matricula=e['matricula'],course_type='Troncal' if core else 'Electiva',eligible_for_minor=False,counted_for_completion=False,recognized_before_enrollment=False,within_deadline=s<=end,eligibility_reason='',duplicate_rows=len(attempts)-1)
        if s>now:reason='Posterior al semestre de corte'
        elif s<start-4:reason='Fuera del período de reconocimiento'
        elif ambiguous:
            reason='Intentos ambiguos en misma asignatura/semestre';reviews.append(f'{c} {semester(s)}: {reason}')
        elif not course or norm(course.get('confirmado'))!='SI':
            reason='Catálogo ausente o clasificación pendiente';reviews.append(f'{c} {semester(s)}: {reason}')
        elif r.get('outcome')=='UNKNOWN' or pd.isna(r.get('nota')) or not 1<=r['nota']<=7:
            reason='Nota o estado final inválido';reviews.append(f'{c}: {reason}')
        elif (r['outcome']=='PASS' and r['nota']<4) or (r['outcome']=='FAIL' and r['nota']>=4):
            reason='Estado final y nota contradictorios';reviews.append(f'{c}: {reason}')
        elif r['outcome']=='FAIL':
            reason='Troncal reprobada' if core else 'Electiva reprobada'
            if core and start<=s<=now:failures.append(s)
        else:
            allowed=True
            if not core and 'Emprendimiento' in m:allowed=special_eligibility(e.get('carrera',''),course)
            if allowed is None:
                reason='Elegibilidad DIFEM/carrera pendiente';reviews.append(f'{c}: {reason}')
            elif not allowed:reason='Electiva no válida para carrera restringida'
            else:
                h['eligible_for_minor']=True;h['recognized_before_enrollment']=s<start
                reason='Posterior al plazo' if s>end else ('Asignatura reconocida previa' if s<start else ('Troncal obligatoria' if core else 'Electiva válida'))
                valid.append((s,c,h))
        h['eligibility_reason']=reason;history.append(h)
    def choose(items):
        cores={}; electives={}
        for s,c,h in sorted(items,key=lambda x:(x[0],x[1])):
            (cores if c in TRONCALES[m] else electives).setdefault(c,(s,c,h))
        return list(cores.values()),list(electives.values())[:3]
    t,el=choose([v for v in valid if v[0]<=end]);ta,ea=choose(valid)
    complete_within_effective=len(t)==2 and len(el)==3
    complete_academically=len(ta)==2 and len(ea)==3
    completion=max(v[0] for v in ta+ea) if complete_academically else None
    over_ordinary=max(0,completion-ordinary_end) if completion is not None else 0
    late=complete_academically and not complete_within_effective
    documented=bool(documented_types)
    probable=late and not documented and over_ordinary==1
    review_late=late and (over_ordinary>=2 or documented)
    chosen_t,chosen_el=(ta,ea) if complete_academically else (t,el)
    # A subsequent course attempt cannot undo an already completed Minor.
    causal=min(failures) if failures else None
    eliminated=causal is not None and (completion is None or causal<=completion)
    if start>now:reviews.append('Inscripción posterior al semestre de corte')
    if reviews:status='REQUIERE REVISIÓN';reason='; '.join(sorted(set(reviews)))
    elif eliminated:status='ELIMINADO POR TRONCAL';reason='Reprobación de troncal en '+semester(causal)
    elif complete_within_effective:
        status='EGRESADO';reason='2 troncales y 3 electivas dentro del plazo autorizado'
    elif probable:
        status='EGRESADO';reason='5/5 completado un semestre después del plazo ordinario'
    elif review_late:
        status='REQUIERE REVISIÓN';reason='5/5 completado con extensión de 2 o más semestres' if over_ordinary>=2 else '5/5 fuera de la excepción documentada'
    elif now>end:status='ELIMINADO POR PLAZO';reason='Plazo finalizado en '+semester(end)
    else:status='CURSANDO';reason='Requisitos pendientes dentro del plazo'
    for s,c,h in chosen_t+chosen_el:
        h['counted_for_completion']=True
        if s>end:h['eligibility_reason']='Aprobación contada con probable excepcionalidad' if probable else 'Aprobación 5/5 fuera del plazo autorizado; requiere revisión'
    for s,c,h in valid:
        if s<=end and not h['counted_for_completion']:h['eligibility_reason']='Asignatura adicional o aprobación repetida'
    alert='CRÍTICA' if status=='CURSANDO' and now==end else ('PREVENTIVA' if status=='CURSANDO' and now==end-1 else '')
    base['extra_semesters']=extra_count
    exception_type=(' / '.join(sorted(documented_types)) if documented and complete_academically else ('PROBABLE_HISTORICAL_EXCEPTION' if probable else ''))
    base.update(status=status,status_reason=reason,ordinary_deadline_semester=semester(ordinary_end),deadline_semester=semester(end),completion_semester=semester(completion) if completion is not None else '',semesters_over_deadline=over_ordinary,probable_exceptionality=bool(probable and status=='EGRESADO'),exception_type=exception_type,graduation_semester=semester(completion) if completion is not None and status=='EGRESADO' else '',troncales_required=2,electives_required=3,troncales_completed=len(chosen_t),electives_completed=len(chosen_el),total_completed=len(chosen_t)+len(chosen_el),pending_troncales=', '.join(c for c in TRONCALES[m] if c not in [v[1] for v in chosen_t]),pending_electives=3-len(chosen_el),total_pending=5-len(chosen_t)-len(chosen_el),alert_level=alert,exception_count=sum(start<=s<=end for s in excluded),completed_out_of_time=late,requires_review=bool(reviews) or status=='REQUIERE REVISIÓN',causal_semester=semester(causal) if eliminated else (semester(end+1) if status=='ELIMINADO POR PLAZO' else ''),history=history)
    return base
