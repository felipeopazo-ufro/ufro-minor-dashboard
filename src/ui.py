from datetime import datetime,timezone
import json
import pandas as pd
import streamlit as st
from .auth import require_admin
from .data_loader import load_source,validate_upload
from .pipeline import process
from .catalog import build_catalog
from .semesters import ordinal
from .official import load_official,apply_official,OFFICIAL_FILE
from .configuration import read_csv,validate_courses,validate_exceptions
from .storage import FILES
from .excel import excel_bytes
from .dirae import dirae_tables
from .reconciliation import reconcile
from .cleaning import norm
from .semesters import normalize

@st.cache_data(show_spinner=False,max_entries=4,ttl=900)
def compute(files):
    sources={k:load_source(k,files[v]) for k,v in FILES.items()}
    settings=json.loads(files['settings.json'])
    courses=validate_courses(files['minor_courses.csv'])
    exceptions=read_csv(files['exceptions.csv']).to_dict('records')
    result=process(sources,settings['current_semester'],courses,exceptions)
    result=apply_official(result,load_official(files[OFFICIAL_FILE]) if OFFICIAL_FILE in files else None)
    result['exceptions']=pd.DataFrame(exceptions)
    return result,sources

def download(label,tables,name):
    st.download_button(label,excel_bytes(tables),file_name=name,mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',key=name)

def filters(df,key):
    out=df.copy();cols=st.columns(3)
    for i,(field,label) in enumerate([('minor','Minor'),('carrera','Carrera'),('semester_enrolled','Semestre inscripción')]):
        opts=sorted(out[field].dropna().unique());sel=cols[i].multiselect(label,opts,key=key+field)
        if sel:out=out[out[field].isin(sel)]
    c1,c2=st.columns(2)
    years=c1.multiselect('Año de inscripción',sorted(out.semester_enrolled.str[:4].unique()),key=key+'year')
    states=c2.multiselect('Estado',sorted(out.status.unique()),key=key+'status')
    if years:out=out[out.semester_enrolled.str[:4].isin(years)]
    if states:out=out[out.status.isin(states)]
    return out

def panorama(r,role):
    d=filters(r['enrollments'],'pan');cols=st.columns(5)
    for c,label,value in zip(cols,['Cursando','Egresados','Eliminados','En alerta','Revisión'],[(d.status=='CURSANDO').sum(),(d.status=='EGRESADO').sum(),d.status.str.startswith('ELIMINADO').sum(),(d.alert_level!='').sum(),d.requires_review.sum()]):c.metric(label,int(value))
    if not r.get('official',pd.DataFrame()).empty:
        o=r['official'];st.info(f'Fuente oficial Inglés: {len(o)} estudiantes, {int((o.official_total==5).sum())} completados (5/5). Este total incluye casos pendientes de vincular al padrón de inscritos.')
    st.caption(f'{len(d):,} participaciones · {d.matricula.nunique():,} personas · semestre de corte {r["current"]}')
    a,b=st.columns(2)
    with a:st.subheader('Participaciones por Minor');st.bar_chart(d.groupby('minor').size())
    with b:st.subheader('Estados');st.bar_chart(d.groupby('status').size())
    st.dataframe(d,hide_index=True,width='stretch')
    if role in ['ADMIN','GESTION']:download('Descargar panorama',{'Participaciones':d},'panorama_minor.xlsx')

def search(r):
    q=st.text_input('Buscar por matrícula o nombre (sin depender de tildes)')
    if not q:return
    d=r['enrollments'];mask=d.matricula.map(norm).str.contains(norm(q),regex=False)|d.nombre.map(norm).str.contains(norm(q),regex=False);found=d[mask]
    if found.empty:st.info('No se encontraron estudiantes inscritos.');return
    choices={x['enrollment_id']:f"{x['nombre']} · {x['matricula']} · {x['minor']} · {x['semester_enrolled']}" for x in found.to_dict('records')}
    eid=st.selectbox('Participación Minor',list(choices),format_func=choices.get);e=found[found.enrollment_id==eid].iloc[0]
    st.subheader(e.nombre);st.write(f'{e.carrera} · {e.minor}');st.info(f'{e.status} — {e.status_reason}')
    if e.get('official_linked',False):
        st.write(f'Avance oficial UFRO: {e.official_cores}/2 troncales · {e.official_electives}/3 electivas · {e.official_total}/5 total')
        st.caption(f'Fuente del estado: {e.status_source}. Fecha oficial de plan completo: {e.official_completion_date or "No informada"}. Estado del alumno: {e.official_student_state}.')
    st.caption('Respaldo calculado a partir de calificaciones:')
    a,b,c=st.columns(3);a.metric('Troncales',f'{int(e.troncales_completed)}/2');b.metric('Electivas',f'{int(e.electives_completed)}/3');c.metric('Total',f'{int(e.total_completed)}/5')
    st.write(f'Inscripción: {e.semester_enrolled} · Límite calculado: {e.deadline_semester} · Egreso calculado: {e.graduation_semester or "No determinado"} · Excepciones: {int(e.exception_count)}')
    st.write(f'Pendientes según calificaciones: troncales: {e.pending_troncales or "Ninguna"}. Electivas pendientes: {int(e.pending_electives)}.')
    ex=r.get('exceptions',pd.DataFrame())
    if not ex.empty:
        ex=ex[(ex.matricula==e.matricula)&(ex.minor==e.minor)]
        if not ex.empty:st.write('Excepciones registradas');st.dataframe(ex,hide_index=True,width='stretch')
    h=r['history'];h=h[h.enrollment_id==eid].copy()
    if h.empty:st.info('Sin calificaciones registradas.');return
    h['Cuenta para Minor']=h.counted_for_completion.map({True:'Sí',False:'No'})
    st.dataframe(h[['codigo','nombre_asignatura','course_type','semester','nota','estado_final','Cuenta para Minor','eligibility_reason','source_row']],hide_index=True,width='stretch')

def dirae(r):
    d=filters(r['enrollments'],'dirae');d=d[d.status=='EGRESADO']
    a,b=st.columns(2);sem=a.multiselect('Semestre de egreso',sorted(d.graduation_semester.unique()));years=b.multiselect('Año de egreso',sorted(d.graduation_semester.str[:4].unique()))
    if sem:d=d[d.graduation_semester.isin(sem)]
    if years:d=d[d.graduation_semester.str[:4].isin(years)]
    st.caption('Cumplimiento académico calculado. Antes de tramitar certificados, DIRAE debe verificar el cierre de actas. La exportación no emite un certificado oficial.')
    tables=dirae_tables(r,d)
    # Scope validation sheet to selected participants; DIRAE never receives unrelated cases.
    tables['VALIDACIONES']=r['quality'][r['quality'].matricula.isin(d.matricula)]
    st.metric('Participaciones con cinco asignaturas listas',len(tables['RESUMEN ESTUDIANTES']));
    if not tables['EGRESADOS POR RESPALDAR'].empty:
        st.warning('Hay egresos reconocidos que aún necesitan conciliar el detalle de asignaturas. No se generan filas de certificación para ellos.');st.dataframe(tables['EGRESADOS POR RESPALDAR'],hide_index=True,width='stretch')
    st.dataframe(tables['DIRAE'],hide_index=True,width='stretch')
    download('Descargar Vista DIRAE',tables,'vista_dirae.xlsx')

def lists(r,page):
    d=filters(r['enrollments'],page)
    if page=='ALERTAS':d=d[d.alert_level!='']
    else:
        group=st.radio('Mostrar',['Eliminaciones oficiales','Causales calculadas y pendientes','Renuncias oficiales'])
        if group=='Eliminaciones oficiales':d=d[d.status=='ELIMINADO OFICIAL']
        elif group=='Renuncias oficiales':d=d[d.status=='RENUNCIA OFICIAL']
        else:d=d[(d.status=='ELIMINADO POR TRONCAL')|d.requires_review]
    st.dataframe(d,hide_index=True,width='stretch');download('Descargar Excel',{page:d},page.lower()+'.xlsx')

def validation(r,sources):
    if not r.get('official_unmatched',pd.DataFrame()).empty:
        st.warning('Registros oficiales sin participación única: revise inscripción o reinscripción. No se incorporan ni asignan silenciosamente.');st.dataframe(r['official_unmatched'][['matricula','Nombre','Ingreso Minor','Total']],hide_index=True,width='stretch')
    q=r['quality'];levels=st.multiselect('Severidad',list(q.nivel.unique()));types=st.multiselect('Tipo de hallazgo',sorted(q.tipo.unique()))
    if levels:q=q[q.nivel.isin(levels)]
    if types:q=q[q.tipo.isin(types)]
    st.dataframe(q,hide_index=True,width='stretch')
    download('Descargar calidad',{'Resumen':q.groupby(['nivel','tipo']).size().reset_index(name='Cantidad'),'Hallazgos':q},'data_quality_report.xlsx')
    download('Descargar conciliación con Looker',reconcile(r,sources['seguimiento']),'reconciliation_report.xlsx')

def commit_candidate(storage,files,version,candidate,actor,role,changes):
    require_admin(role)
    audit=json.loads(candidate.get('audit.json',b'[]'))
    audit.append({'timestamp':datetime.now(timezone.utc).isoformat(),'actor':actor,'changes':changes,'previous_version':version})
    candidate['audit.json']=json.dumps(audit,ensure_ascii=False).encode()
    storage.write(candidate,version);st.session_state.pop('snapshot',None);st.session_state.pop('candidate',None);compute.clear();st.success('Actualización guardada.');st.rerun()

def update(r,files,version,storage,actor,role):
    require_admin(role)
    st.write('Reemplace bases acumulativas completas. Validar prepara una comparación antes de guardar.')
    candidate=dict(files);changed=[]
    for k,title in [('inscritos','Inscritos'),('calificaciones','Calificaciones'),('master','Padrón máster'),('seguimiento','Seguimiento histórico de referencia')]:
        up=st.file_uploader(title,type=['xlsx'],key=k)
        if up:
            data=up.getvalue();candidate[FILES[k]]=data;changed.append(k)
    official_up=st.file_uploader('Avance oficial Minor en Inglés (.xls o .xlsx)',type=['xls','xlsx'],key='official_upload')
    if official_up:candidate[OFFICIAL_FILE]=official_up.getvalue();changed.append('oficial')
    if st.button('Validar y procesar',disabled=not changed):
        try:
            row_counts={}
            for k in changed:
                row_counts[k]=len(load_official(candidate[OFFICIAL_FILE])) if k=='oficial' else len(validate_upload(k,candidate[FILES[k]]))
            if 'calificaciones' in changed or 'seguimiento' in changed:
                observed=build_catalog(load_source('calificaciones',candidate[FILES['calificaciones']]),load_source('seguimiento',candidate[FILES['seguimiento']]))
                existing=read_csv(candidate['minor_courses.csv']); additions=[]
                for item in observed.to_dict('records'):
                    same=existing[(existing.codigo==item['codigo'])&(existing.minor==item['minor'])]
                    covered=any(ordinal(v['semestre_desde'])<=ordinal(item['semestre_desde'])<=ordinal(v['semestre_hasta']) for v in same.to_dict('records'))
                    if not covered:additions.append(item)
                if additions:candidate['minor_courses.csv']=pd.concat([existing,pd.DataFrame(additions)],ignore_index=True).to_csv(index=False).encode()
                row_counts['Vigencias nuevas del catálogo']=len(additions)
            st.write({'Filas validadas':row_counts})
            new,_=compute(candidate)
            # Existing valid participation cannot silently disappear without explicit review below.
            old_ids=set(r['enrollments'].enrollment_id);new_ids=set(new['enrollments'].enrollment_id)
            st.session_state['candidate']=(candidate,version,changed,len(new_ids-old_ids),len(old_ids-new_ids),new['enrollments'].status.value_counts().to_dict())
        except Exception as e:st.error(str(e) if isinstance(e,ValueError) else 'No se pudo validar el archivo. Revise estructura y formato.')
    pending=st.session_state.get('candidate')
    if pending and pending[1]==version:
        cand,ver,changes,added,removed,states=pending
        st.write({'Altas':added,'Participaciones retiradas':removed,'Estados nuevos':states})
        st.warning('Guardar aplicará la versión validada. Si vuelve a elegir archivos, presione Validar y procesar nuevamente.')
        accepted=st.checkbox('Revisé las altas, retiros y estados de la versión validada.')
        if st.button('Guardar versión validada',disabled=not accepted):commit_candidate(storage,files,version,cand,actor,role,changes)

def configuration(r,files,version,storage,actor,role):
    require_admin(role);settings=json.loads(files['settings.json'])
    semester=st.text_input('Semestre actual',settings['current_semester'])
    st.caption('El catálogo es por código, Minor y vigencia. SI/NO/REVISAR define la elegibilidad para carreras restringidas. Confirme equivalencias institucionales con respaldo antes de cambiarlas.')
    courses=st.data_editor(read_csv(files['minor_courses.csv']),num_rows='dynamic',hide_index=True,width='stretch',key='courses_editor')
    st.subheader('Movilidad, retiro y prórrogas')
    st.caption('Tipos: Movilidad, Postergación, Retiro temporal o Prórroga extraordinaria. Para una prórroga, indique semestres_extension y la resolución/autorización en observacion. No se aplican extensiones sin aprobación.')
    exception_data=read_csv(files['exceptions.csv'])
    if 'semestres_extension' not in exception_data:exception_data['semestres_extension']=''
    exceptions=st.data_editor(exception_data,num_rows='dynamic',hide_index=True,width='stretch',key='exceptions_editor')
    if st.button('Validar y guardar configuración'):
        try:
            settings['current_semester']=normalize(semester)
            c=courses.fillna('').to_csv(index=False).encode();ex=exceptions.fillna('').to_csv(index=False).encode()
            validate_courses(c);validate_exceptions(ex,r['enrollments'])
            candidate=dict(files);candidate.update({'settings.json':json.dumps(settings).encode(),'minor_courses.csv':c,'exceptions.csv':ex})
            compute(candidate);commit_candidate(storage,files,version,candidate,actor,role,['configuración','catálogo','excepciones'])
        except ValueError as e:st.error(str(e))
    st.subheader('Usuarios y roles');st.caption('La lista autorizada se administra en los secretos de Streamlit, sección [users]. Sólo ADMIN modifica datos; CONSULTA no tiene exportación XLSX; DIRAE sólo accede a certificación.')
    st.subheader('Historial de actualizaciones');st.dataframe(pd.DataFrame(json.loads(files.get('audit.json',b'[]'))),hide_index=True)
