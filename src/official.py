"""Administrative evidence layer. Never fabricates a grade, deadline or enrollment."""
from io import BytesIO
import re
import pandas as pd
from .cleaning import matricula,text,norm,MINORS
OFFICIAL_FILE='avance_oficial_ingles.xlsx'
RECONCILIATION_FILE='official_reconciliation_overrides.csv'
REQUIRED=['Matrícula','Nombre','Carrera','Estado Alumno','Ingreso Minor','Eliminación','Renuncia','Plan Completo','Certificado','Troncal','Electivas','Total']

def count(value,denominator):
    m=re.fullmatch(r'\s*(\d+)\s*(?:de|/)\s*(\d+)\s*',text(value),re.I)
    if not m or int(m[2])!=denominator or not 0<=int(m[1])<=denominator:
        raise ValueError(f'Avance oficial inválido: se esperaba n de {denominator}.')
    return int(m[1])

def date_text(v):
    if not text(v):return ''
    try:
        t=pd.to_datetime(v,dayfirst=True,errors='raise') if isinstance(v,str) else pd.Timestamp(v)
        return t.strftime('%Y-%m-%d')
    except (ValueError,TypeError):raise ValueError('Fecha inválida en avance oficial UFRO.')

def load_official(data):
    try:
        d=pd.read_excel(BytesIO(data),sheet_name='Estudiantes Minor',dtype=object,engine='openpyxl' if data[:2]==b'PK' else 'xlrd').dropna(how='all')
    except Exception as e:raise ValueError('No se pudo leer la hoja Estudiantes Minor del archivo oficial.') from e
    if set(REQUIRED)-set(d):raise ValueError('Faltan columnas del avance oficial: '+', '.join(sorted(set(REQUIRED)-set(d))))
    if len(d.columns)<15 or d.columns[14]!='Total':raise ValueError('La columna O del archivo oficial debe ser Total.')
    if d.empty:raise ValueError('El avance oficial no contiene estudiantes.')
    d['matricula']=d['Matrícula'].map(matricula)
    if (d.matricula=='').any() or d.matricula.duplicated().any():raise ValueError('El avance oficial contiene matrículas vacías o repetidas.')
    d['official_total']=d.Total.map(lambda v:count(v,5))
    d['official_cores']=d.Troncal.map(lambda v:count(v,2));d['official_electives']=d.Electivas.map(lambda v:count(v,3))
    if (d.official_total!=d.official_cores+d.official_electives).any():raise ValueError('Total oficial no coincide con troncales más electivas.')
    for original,new in [('Ingreso Minor','official_enrollment_date'),('Plan Completo','official_completion_date'),('Eliminación','official_elimination_date'),('Renuncia','official_resignation_date'),('Certificado','official_certificate_date')]:d[new]=d[original].map(date_text)
    d['official_student_state']=d['Estado Alumno'].map(text);d['source_row']=d.index+2
    return d

def apply_official(result,official=None,adjudications=None):
    """Preserve computed evidence; official 5/5 governs completion, not invented DIRAE rows."""
    e=result['enrollments'].copy();issues=[];off=official if official is not None else pd.DataFrame()
    for field in ['status','status_reason','requires_review','graduation_semester']:
        e['calculated_'+field]=e[field]
    e['status_source']='CÁLCULO';e['dirae_ready']=(e.status=='EGRESADO')&~e.requires_review
    e['official_linked']=False;e['official_total']=-1;e['official_cores']=-1;e['official_electives']=-1
    for c in ['official_completion_date','official_enrollment_date','official_elimination_date','official_resignation_date','official_certificate_date','official_student_state']:e[c]=''
    def issue(mat,detail,level='ADVERTENCIA'):
        issues.append(dict(nivel=level,tipo='Contraste oficial / plazo',matricula=mat,detalle=detail,fuente='avance_oficial_ingles',fila_origen=''))
    decisions={}
    for row in adjudications or []:
        mat=matricula(row.get('matricula',''))
        if mat and mat not in decisions:decisions[mat]=row
    # Without full movements, passing six ordinary semesters is an administrative review trigger.
    overdue=e.status=='ELIMINADO POR PLAZO'
    e.loc[overdue,'status']='PLAZO EXCEDIDO POR REVISAR';e.loc[overdue,'status_reason']='Plazo ordinario excedido. Verificar extensiones, retiro temporal y movilidad antes de confirmar eliminación.'
    e.loc[overdue,'requires_review']=True;e.loc[overdue,'dirae_ready']=False;e.loc[overdue,'alert_level']='REVISAR PLAZO'
    for mat in e.loc[overdue,'matricula']:issue(mat,'Plazo calculado excedido sin antecedentes completos de excepciones.')
    for a in off.to_dict('records'):
        mask=(e.matricula==a['matricula'])&(e.minor==MINORS[0]);idx=e.index[mask]
        if len(idx)!=1:
            issue(a['matricula'],'Sin participación de Inglés única: no se aplica el estado oficial automáticamente.','ERROR')
            if len(idx)>1:
                e.loc[idx,'status']='REQUIERE REVISIÓN';e.loc[idx,'requires_review']=True;e.loc[idx,'dirae_ready']=False
            continue
        i=idx[0];r=e.loc[i];e.at[i,'official_linked']=True
        for c in e.columns:
            if c.startswith('official_') and c in a:e.at[i,c]=a[c]
        done=a['official_total']==5;removed=bool(a['official_elimination_date']);resigned=bool(a['official_resignation_date'])
        if (done and (removed or resigned)) or (removed and resigned):
            e.at[i,'status']='REQUIERE REVISIÓN';e.at[i,'requires_review']=True;e.at[i,'dirae_ready']=False;e.at[i,'status_reason']='El archivo oficial contiene estados administrativos contradictorios.';issue(a['matricula'],e.at[i,'status_reason'],'ERROR');continue
        if done:
            if r.calculated_status=='ELIMINADO POR TRONCAL' and r.completion_semester:
                e.at[i,'dirae_ready']=False
                issue(a['matricula'],'5/5 oficial no elimina la causal académica de reprobación de troncal.','ERROR')
                continue
            if (r.calculated_status=='REQUIERE REVISIÓN' and r.completion_semester
                    and r.semesters_over_deadline>=2 and not r.exception_type):
                e.at[i,'dirae_ready']=False
                issue(a['matricula'],'5/5 oficial no acredita extensión de dos o más semestres; revisar excepción documentada.')
                continue
            e.at[i,'status']='EGRESADO';e.at[i,'status_source']='OFICIAL UFRO';e.at[i,'status_reason']='Finalización confirmada: Total oficial 5 de 5.';e.at[i,'alert_level']=''
            if r.probable_exceptionality:
                e.at[i,'status_reason']=r.calculated_status_reason+'; avance oficial 5 de 5.'
            e.at[i,'requires_review']=bool(r.calculated_requires_review)
            # Only grade-based, unambiguous valid completions can create the 5-course submission.
            e.at[i,'dirae_ready']=bool(r.calculated_status=='EGRESADO' and not r.calculated_requires_review)
            if not e.at[i,'dirae_ready']:
                e.at[i,'status_reason']+=' Falta conciliar el detalle de cinco asignaturas para exportación DIRAE.'
                issue(a['matricula'],'5/5 oficial reconocido. Conciliar respaldo académico sin inventar extensión ni fecha.')
        elif removed or resigned:
            e.at[i,'status']='ELIMINADO OFICIAL' if removed else 'RENUNCIA OFICIAL';e.at[i,'status_source']='OFICIAL UFRO';e.at[i,'status_reason']='Registro administrativo explícito en el archivo oficial del Minor.';e.at[i,'requires_review']=False;e.at[i,'dirae_ready']=False;e.at[i,'alert_level']='';e.at[i,'graduation_semester']=''
        else:
            decision=decisions.get(a['matricula'],{})
            if (decision.get('minor')==MINORS[0]
                    and decision.get('decision')=='ACADEMIC_5_OF_5_ONE_SEMESTER_LATE'
                    and r.calculated_status=='EGRESADO'
                    and bool(r.probable_exceptionality)
                    and int(r.total_completed)==5 and int(r.troncales_completed)==2
                    and int(r.electives_completed)>=3 and not r.causal_semester
                    and a['official_total']==4):
                e.at[i,'status']='EGRESADO';e.at[i,'status_source']='CÁLCULO ACADÉMICO / RECONCILIACIÓN'
                e.at[i,'status_reason']='5/5 académico comprobado; un semestre después del plazo ordinario. Avance histórico registraba 4/5.'
                e.at[i,'probable_exceptionality']=True;e.at[i,'exception_type']='PROBABLE_HISTORICAL_EXCEPTION'
                e.at[i,'requires_review']=False;e.at[i,'dirae_ready']=True;e.at[i,'alert_level']=''
                issue(a['matricula'],'Reconciliación de caso individual: la evidencia académica actual acredita 5/5 y la fuente histórica conserva 4/5.')
                continue
            if (decision.get('minor')==MINORS[0]
                    and decision.get('decision')=='ACADEMIC_5_OF_5_ONE_SEMESTER_LATE'
                    and a['official_total']==4):
                if int(r.troncales_completed)<2:detail='No cumple las 2 troncales requeridas.'
                elif int(r.electives_completed)<3:detail='No cumple las 3 electivas válidas requeridas.'
                elif r.causal_semester:detail='Existe reprobación de troncal en '+str(r.causal_semester)+'.'
                elif not r.completion_semester:detail='No hay semestre de completitud académica comprobado.'
                elif int(r.semesters_over_deadline)!=1:detail='La completitud no ocurrió exactamente un semestre después del límite ordinario.'
                else:detail='Los cinco requisitos no están respaldados por las calificaciones actuales.'
                e.at[i,'status']='REQUIERE REVISIÓN';e.at[i,'status_source']='RECONCILIACIÓN ACADÉMICA'
                e.at[i,'status_reason']=detail+' Avance histórico registraba 4/5.'
                e.at[i,'probable_exceptionality']=False;e.at[i,'exception_type']=''
                e.at[i,'requires_review']=True;e.at[i,'dirae_ready']=False;e.at[i,'graduation_semester']=''
                issue(a['matricula'],e.at[i,'status_reason'],'ERROR')
                continue
            if r.calculated_status=='EGRESADO':
                e.at[i,'status']='REQUIERE REVISIÓN';e.at[i,'status_reason']='El cálculo completa requisitos pero el registro oficial tiene menos de 5/5.';e.at[i,'requires_review']=True;e.at[i,'dirae_ready']=False;e.at[i,'graduation_semester']='';issue(a['matricula'],e.at[i,'status_reason'],'ERROR')
            state=norm(a['official_student_state'])
            if any(t in state for t in ['POSTERGACION','RETIRO TEMPORAL','MOVILIDAD']):
                if e.at[i,'status']=='CURSANDO':e.at[i,'status']='PAUSA ACADÉMICA REGISTRADA';e.at[i,'status_source']='OFICIAL UFRO'
                e.at[i,'requires_review']=True;e.at[i,'dirae_ready']=False;e.at[i,'alert_level']='REVISAR PAUSA';e.at[i,'status_reason']+=' Pausa actual registrada; faltan los semestres afectados para ajustar el límite.'
                issue(a['matricula'],'Pausa académica actual. No permite inferir duración ni reconstruir movimientos anteriores.')
    e.loc[e.status!='EGRESADO','probable_exceptionality']=False
    e.loc[(e.status!='EGRESADO')&(e.exception_type=='PROBABLE_HISTORICAL_EXCEPTION'),'exception_type']=''
    result=dict(result);result['enrollments']=e;result['official']=off
    pending=[]
    for a in off.to_dict('records'):
        matches=e[(e.matricula==a['matricula'])&(e.minor==MINORS[0])]
        if len(matches)!=1:pending.append(a)
    result['official_unmatched']=pd.DataFrame(pending)
    if issues:result['quality']=pd.concat([result['quality'],pd.DataFrame(issues)],ignore_index=True)
    return result
