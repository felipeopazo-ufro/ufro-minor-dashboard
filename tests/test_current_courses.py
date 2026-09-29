import pandas as pd
from src.cleaning import MINORS,TRONCALES
from src.current_courses import DISPLAY_COLUMNS,attach_current_courses,student_history
from src.dirae import dirae_tables

ENGLISH=MINORS[0]; ENTRE=MINORS[1]

def course(code,minor=ENGLISH,kind=None):
    return dict(codigo=code,nombre='Course '+code,minor=minor,tipo=kind or ('Troncal' if code in TRONCALES[minor] else 'Electiva'),
        semestre_desde='2000-1',semestre_hasta='2100-2',unidad_academica='Formación General',
        valida_ing_comercial='SI',valida_contador_auditor='SI',confirmado='SI',observaciones='Test')

def participation(minor=ENGLISH,status='CURSANDO',count=2):
    return dict(enrollment_id='001|'+minor+'|2025-1',matricula='001',nombre='Synthetic Student',carrera='Derecho',minor=minor,
        semester_enrolled='2025-1',status=status,status_reason='Synthetic',total_completed=count,troncales_completed=1,
        electives_completed=count-1,requires_review=False,deadline_semester='2027-2',graduation_semester='')

def history_row(code,semester='2025-1',outcome='PASS',counted=True,prior=False,minor=ENGLISH):
    return dict(enrollment_id='001|'+minor+'|2025-1',matricula='001',codigo=code,canonical_course_code=code,
        nombre_asignatura='Course '+code,course_type='Troncal' if code in TRONCALES[minor] else 'Electiva',semester=semester,
        nota=5.0,estado_final='APROBADA' if outcome=='PASS' else 'REPROBADA',outcome=outcome,source='calificaciones',
        source_row=2,unidad_academica='Formación General',eligible_for_minor=True,counted_for_completion=counted,
        recognized_before_enrollment=prior,currently_enrolled=False,eligibility_reason='')

def registration(code,mat='001',state='Inscrita',name=None):
    return dict(matricula=mat,codigo=code,canonical_course_code=code,nombre_asignatura=name or 'Course '+code,
        unidad_academica='Formación General',enrollment_status=state,currently_enrolled=(state=='Inscrita'),source_row=2)

def result(minor=ENGLISH,status='CURSANDO',count=2,history=None,courses=None):
    return dict(enrollments=pd.DataFrame([participation(minor,status,count)]),
        history=pd.DataFrame(history or []),quality=pd.DataFrame(columns=['nivel','tipo','matricula','detalle','fuente','fila_origen']),
        courses=pd.DataFrame(courses or [course('DFI183',minor),course('DFI185',minor),course('E1',minor,'Electiva')]))

def test_current_registration_does_not_increase_total_completed():
    r=attach_current_courses(result(history=[history_row('DFI183'),history_row('E1')]),pd.DataFrame([registration('DFI185')]),'2026-2')
    assert r['enrollments'].iloc[0].total_completed==2

def test_current_core_is_not_approved():
    r=attach_current_courses(result(history=[history_row('DFI183')]),pd.DataFrame([registration('DFI185')]),'2026-2')
    current=r['history'][r['history'].currently_enrolled==True]
    assert len(current)==1 and current.iloc[0].course_type=='Troncal' and pd.isna(current.iloc[0].nota)
    assert r['enrollments'].iloc[0].troncales_completed==1

def test_current_core_does_not_trigger_elimination():
    r=attach_current_courses(result(status='CURSANDO',history=[history_row('DFI183')]),pd.DataFrame([registration('DFI185')]),'2026-2')
    assert r['enrollments'].iloc[0].status=='CURSANDO'

def test_current_elective_is_rendered_as_cursando():
    r=attach_current_courses(result(history=[history_row('DFI183')]),pd.DataFrame([registration('E1')]),'2026-2')
    view=student_history(r['history'],'001|'+ENGLISH+'|2025-1')
    assert 'CURSANDO' in set(view['Situación']) and 'E1' in set(view['Código'])

def test_two_approved_plus_one_current_is_two_of_five_and_one_current():
    r=attach_current_courses(result(history=[history_row('DFI183'),history_row('E1')]),pd.DataFrame([registration('DFI185')]),'2026-2')
    e=r['enrollments'].iloc[0]
    assert e.total_completed==2 and e.current_minor_courses_count==1

def test_course_confirmed_only_for_other_minor_is_not_attached():
    r=attach_current_courses(result(history=[history_row('DFI183')],courses=[course('DFI183'),course('DFI165',ENTRE)]),pd.DataFrame([registration('DFI165')]),'2026-2')
    assert not (r['history'].get('currently_enrolled',pd.Series(dtype=bool))==True).any()
    assert 'Asignatura actual asociada a otro Minor' in set(r['quality'].tipo)

def test_unknown_current_code_generates_validation_issue():
    r=attach_current_courses(result(),pd.DataFrame([registration('ZZZ999')]),'2026-2')
    assert 'Código actual no reconocido para Minor' in set(r['quality'].tipo)

def test_non_inscrita_status_is_not_displayed_as_current():
    r=attach_current_courses(result(),pd.DataFrame([registration('E1',state='Retirada')]),'2026-2')
    assert r['enrollments'].iloc[0].current_minor_courses_count==0
    assert 'Inscripción con estado distinto de Inscrita' in set(r['quality'].tipo)

def test_prior_approved_and_current_are_separate_rows():
    r=attach_current_courses(result(history=[history_row('DFI183','2024-2',prior=True)]),pd.DataFrame([registration('E1')]),'2026-2')
    view=student_history(r['history'],'001|'+ENGLISH+'|2025-1')
    assert list(view['Situación'])==['APROBADA — RECONOCIDA PREVIA','CURSANDO']

def test_missing_current_master_does_not_remove_participation():
    original=result();r=attach_current_courses(original,pd.DataFrame([registration('E1')]),'2026-2')
    assert len(r['enrollments'])==1 and r['enrollments'].iloc[0].matricula=='001'

def test_additional_approved_course_remains_visible():
    h=[history_row('DFI183'),history_row('E1'),history_row('E2',counted=False)]
    r=attach_current_courses(result(history=h,courses=[course('DFI183'),course('E1','Minor en Inglés','Electiva'),course('E2','Minor en Inglés','Electiva')]),pd.DataFrame(),'2026-2')
    view=student_history(r['history'],'001|'+ENGLISH+'|2025-1')
    assert view.loc[view['Código']=='E2','Situación'].iloc[0]=='APROBADA — ADICIONAL'

def test_prior_recognition_has_readable_status_and_flag():
    r=attach_current_courses(result(history=[history_row('E1','2024-2',prior=True)]),pd.DataFrame(),'2026-2')
    view=student_history(r['history'],'001|'+ENGLISH+'|2025-1')
    assert view.iloc[0]['Situación']=='APROBADA — RECONOCIDA PREVIA' and view.iloc[0]['Reconocimiento previo']=='Sí'

def test_failed_elective_and_later_pass_are_both_shown():
    h=[history_row('E1','2024-2','FAIL',False),history_row('E1','2025-1','PASS',True)]
    r=attach_current_courses(result(history=h),pd.DataFrame(),'2026-2')
    view=student_history(r['history'],'001|'+ENGLISH+'|2025-1')
    assert list(view['Situación'])==['REPROBADA','APROBADA']

def test_current_rows_never_appear_in_dirae():
    h=[history_row(c,counted=True) for c in ['DFI183','DFI185','E1','E2','E3']]
    r=result(status='EGRESADO',count=5,history=h,courses=[course(c) for c in ['DFI183','DFI185','E1','E2','E3']])
    r=attach_current_courses(r,pd.DataFrame([registration('E4')]),'2026-2')
    tables=dirae_tables(r)
    assert len(tables['DIRAE'])==5 and not tables['DIRAE']['Código_asig'].eq('E4').any()

def test_history_exposes_only_requested_readable_columns():
    view=student_history(pd.DataFrame([history_row('DFI183')]),'001|'+ENGLISH+'|2025-1')
    assert list(view.columns)==DISPLAY_COLUMNS
    assert not any('Cuenta' in c for c in view.columns)

def test_current_registration_name_and_career_conflicts_are_validation_only():
    row=registration('E1');row['carrera']='Ingeniería Comercial'
    r=attach_current_courses(result(),pd.DataFrame([row]),'2026-2')
    assert {'Conflicto carrera actual'}.issubset(set(r['quality'].tipo))
    assert r['enrollments'].iloc[0].status=='CURSANDO'

def test_duplicate_current_course_is_counted_once_and_flagged():
    r=attach_current_courses(result(),pd.DataFrame([registration('E1'),registration('E1')]),'2026-2')
    assert r['enrollments'].iloc[0].current_minor_courses_count==1
    assert 'Inscripción actual duplicada' in set(r['quality'].tipo)
