import pytest,pandas as pd
from src.status_engine import calculate_minor_status
from src.semesters import add,ordinal
from src.cleaning import MINORS,TRONCALES,matricula
M=MINORS[0]
def enrollment(m=M,s='2024-1'):
 return dict(matricula='001',nombre='Persona sintética',carrera='Derecho',minor=m,semester_enrolled=s,enrollment_id='001|'+m+'|'+s)
def catalog(m=M):
 return pd.DataFrame([dict(codigo=c,nombre=c,minor=m,tipo='Troncal' if c in TRONCALES[m] else 'Electiva',semestre_desde='2000-1',semestre_hasta='2100-2',confirmado='SI',observaciones='Reglamento',valida_ing_comercial='NO',valida_contador_auditor='NO') for c in TRONCALES[m]+['E1','E2','E3','E4']])
def grade(c,s='2024-1',pass_=True,m=M):
 return dict(matricula='001',minor=m,codigo=c,semester=s,nota=5. if pass_ else 3.,outcome='PASS' if pass_ else 'FAIL',estado_final='APROBADA' if pass_ else 'REPROBADA',nombre_asignatura=c)
def complete(m=M,s='2024-1'):return [grade(c,s,m=m) for c in TRONCALES[m]+['E1','E2','E3']]
def calc(g,e=None,now='2026-2',ex=None):
 e=e or enrollment();return calculate_minor_status(e,g,catalog(e['minor']),ex or [],now)
def test_1_completed():assert calc(complete())['status']=='EGRESADO'
def test_2_pending():assert calc([])['status']=='CURSANDO'
def test_3_failed_core():
 g=[grade('DFI183','2024-1',False)]+complete(s='2024-2');assert calc(g)['status']=='ELIMINADO POR TRONCAL'
def test_4_late():
 r=calc(complete(s='2027-1'),now='2027-1');assert r['status']=='ELIMINADO POR PLAZO' and r['completed_out_of_time']
def test_5_three_prior():assert calc([grade('E1','2022-2')])['electives_completed']==1
def test_6_five_prior():assert calc([grade('E1','2021-2')])['electives_completed']==0
def test_7_penultimate():assert calc([],now='2026-1')['alert_level']=='PREVENTIVA'
def test_8_last():assert calc([])['alert_level']=='CRÍTICA'
def test_9_mobility():
 ex=[dict(matricula='001',minor=M,semestre_afectado='2025-1',contabiliza_en_plazo='No',aprobada='Sí')]
 assert calc([],ex=ex)['deadline_semester']=='2027-1'
def test_10_restricted():
 e=enrollment(MINORS[1]);e['carrera']='Ingeniería Comercial';assert calc(complete(MINORS[1]),e)['electives_completed']==0
def test_11_multiple():
 g=complete()+complete(MINORS[1]);assert calc(g)['status']=='EGRESADO';assert calc(g,enrollment(MINORS[1]))['status']=='EGRESADO'
def test_12_previous_electives():
 g=[grade(c,'2023-2') for c in ['E1','E2','E3']]+[grade(c,'2024-2') for c in TRONCALES[M]];assert calc(g)['graduation_semester']=='2024-2'
def test_13_new():
 r=calc([],enrollment(s='2026-2'));assert r['status']=='CURSANDO' and r['total_completed']==0
@pytest.mark.parametrize('s,n,want',[('2024-2',5,'2027-1'),('2024-1',-4,'2022-1'),('2024-1',-1,'2023-2')])
def test_arithmetic(s,n,want):assert add(s,n)==want
@pytest.mark.parametrize('s',['2024-3','NaN','2024',None])
def test_invalid_semester(s):
 with pytest.raises(ValueError):ordinal(s)
def test_ambiguous():
 assert calc([grade('DFI183'),grade('DFI183',pass_=False)])['requires_review']
def test_repeated_course_not_twice():
 r=calc([grade('E1'),grade('E1','2024-2'),grade('E2')]);assert r['electives_completed']==2
def test_previous_core_not_counted():assert calc([grade('DFI183','2023-2')])['troncales_completed']==0
def test_exact_four_prior():assert calc([grade('E1','2022-1')])['electives_completed']==1
def test_future_ignored():assert calc(complete(s='2027-1'))['total_completed']==0
def test_postgraduation_failure():assert calc(complete()+[grade('DFI183','2024-2',False)])['status']=='EGRESADO'
def test_duplicate_exception():
 ex=dict(matricula='001',minor=M,semestre_afectado='2025-1',contabiliza_en_plazo='NO',aprobada='SI');assert calc([],ex=[ex,ex])['exception_count']==1
def test_exception_outside_does_not_revive():
 ex=dict(matricula='001',minor=M,semestre_afectado='2027-2',contabiliza_en_plazo='NO',aprobada='SI');assert calc([],ex=[ex])['deadline_semester']=='2026-2'
def test_unconfirmed_exception():
 ex=dict(matricula='001',minor=M,semestre_afectado='2025-1',contabiliza_en_plazo='NO',aprobada='NO');assert calc([],ex=[ex])['requires_review']
def test_unknown_special():
 e=enrollment(MINORS[1]);e['carrera']='Contador Público y Auditor';c=catalog(MINORS[1]);c['valida_contador_auditor']='REVISAR';r=calculate_minor_status(e,complete(MINORS[1]),c,[],'2026-2');assert r['requires_review']
def test_identifier():assert matricula(' 00120.0 ' )=='00120'
def test_deterministic_selection():
 r=calc(list(reversed(complete()+[grade('E4')])));assert {h['codigo'] for h in r['history'] if h['counted_for_completion']}==set(TRONCALES[M]+['E1','E2','E3'])

def test_invalid_enrollment_has_complete_schema():
 e=enrollment();e['semester_enrolled']='incorrecto';r=calc([],e);assert r['requires_review'] and r['total_completed']==0 and r['deadline_semester']==''

def test_grade_contradiction_blocks():
 g=complete();g[0]['nota']=3.;assert calc(g)['requires_review']
