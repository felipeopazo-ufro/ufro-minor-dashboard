import pytest,pandas as pd
from src.status_engine import calculate_minor_status
from src.semesters import add,ordinal
from src.cleaning import MINORS,TRONCALES,matricula
from src.cleaning import canonical_code,names_compatible
from src.catalog import equivalence_conflicts,unit_eligibility
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
def test_1_completed():
 r=calc(complete());assert r['status']=='EGRESADO' and not r['probable_exceptionality'] and r['semesters_over_deadline']==0
def test_2_pending():assert calc([])['status']=='CURSANDO'
def test_3_failed_core():
 g=[grade('DFI183','2024-1',False)]+complete(s='2024-2');assert calc(g)['status']=='ELIMINADO POR TRONCAL'
def test_4_late():
 r=calc(complete(s='2027-1'),now='2027-1')
 assert r['status']=='EGRESADO' and r['completed_out_of_time']
 assert r['deadline_semester']=='2026-2' and r['completion_semester']=='2027-1'
 assert r['semesters_over_deadline']==1 and r['probable_exceptionality']
 assert r['exception_type']=='PROBABLE_HISTORICAL_EXCEPTION'

@pytest.mark.parametrize('completion,over',[('2027-2',2),('2028-1',3),('2029-1',5)])
def test_later_completion_requires_review(completion,over):
 r=calc(complete(s=completion),now=completion)
 assert r['status']=='REQUIERE REVISIÓN' and r['semesters_over_deadline']==over
 assert r['completion_semester']==completion and not r['probable_exceptionality']
 assert '5/5 completado con extensión de 2 o más semestres' in r['status_reason']

def test_four_of_five_one_semester_late_is_not_graduated():
 r=calc(complete(s='2027-1')[:-1],now='2027-1')
 assert r['status']!='EGRESADO' and not r['probable_exceptionality']

def test_failed_core_still_eliminates_at_one_semester_late():
 r=calc([grade('DFI183','2024-1',False)]+complete(s='2027-1'),now='2027-1')
 assert r['status']=='ELIMINADO POR TRONCAL' and not r['probable_exceptionality']

@pytest.mark.parametrize('kind',['Movilidad estudiantil','Postergación de estudios'])
def test_documented_exception_takes_priority(kind):
 ex=[dict(matricula='001',minor=M,semestre_afectado='2025-1',tipo_excepcion=kind,contabiliza_en_plazo='NO',aprobada='SI')]
 r=calc(complete(s='2027-1'),now='2027-1',ex=ex)
 assert r['status']=='EGRESADO' and r['deadline_semester']=='2027-1'
 assert r['semesters_over_deadline']==1 and not r['probable_exceptionality'] and r['exception_type']==kind
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
def test_previous_core_counted():assert calc([grade('DFI183','2023-2')])['troncales_completed']==1
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

@pytest.mark.parametrize('cip,dfi,m',[('CIP165','DFI165',MINORS[1]),('CIP183','DFI183',MINORS[0]),('CIP185','DFI185',MINORS[0])])
def test_historical_equivalences_count_once(cip,dfi,m):
 e=enrollment(m);r=calc([grade(cip,'2023-2',m=m),grade(dfi,'2024-2',m=m)],e)
 assert r['troncales_completed']==1 and sum(h['counted_for_completion'] for h in r['history'])==1
 assert any(h['codigo']==cip and h['canonical_course_code']==dfi for h in r['history'])

def test_cip_165_exact_four_prior():
 e=enrollment(MINORS[1]);r=calc([grade('CIP165','2022-1',m=MINORS[1])],e)
 assert r['troncales_completed']==1 and r['history'][0]['recognized_before_enrollment']

def test_cip_165_five_prior():
 e=enrollment(MINORS[1]);assert calc([grade('CIP165','2021-2',m=MINORS[1])],e)['troncales_completed']==0

def test_prior_core_and_elective_complete():
 e=enrollment(MINORS[1]);g=[grade(c,'2022-1',m=MINORS[1]) for c in ['CIP165','E1']]
 g += [grade(c,'2024-1',m=MINORS[1]) for c in ['IAE145','E2','E3']]
 r=calc(g,e);assert r['status']=='EGRESADO' and r['total_completed']==5

def test_restricted_prior_elective_not_valid():
 e=enrollment(MINORS[1]);e['carrera']='Ingeniería Comercial'
 r=calc([grade('E1','2022-1',m=MINORS[1])],e)
 assert r['electives_completed']==0

@pytest.mark.parametrize('suffix',['040','044','101','105','140','147','159','163','165','171','183','185'])
def test_historical_code_migration(suffix):
 assert canonical_code('CIP'+suffix)=='DFI'+suffix

@pytest.mark.parametrize('suffix',['044','101','105','140','147','159'])
def test_elective_cip_and_dfi_count_once(suffix):
 m=MINORS[1];c=catalog(m)
 c.loc[len(c)]={'codigo':'DFI'+suffix,'nombre':'Asignatura '+suffix,'minor':m,'tipo':'Electiva',
  'semestre_desde':'2000-1','semestre_hasta':'2100-2','confirmado':'SI','observaciones':'Catálogo',
  'valida_ing_comercial':'SI','valida_contador_auditor':'SI'}
 e=enrollment(m);e['carrera']='Ingeniería Comercial'
 r=calculate_minor_status(e,[grade('CIP'+suffix,'2023-2',m=m),grade('DFI'+suffix,'2024-1',m=m)],c,[],'2026-2')
 assert r['electives_completed']==1
 assert sum(h['counted_for_completion'] for h in r['history'])==1
 assert any(h['codigo']=='CIP'+suffix and h['canonical_course_code']=='DFI'+suffix for h in r['history'])

def test_mismatched_course_names_block_equivalence():
 m=MINORS[1]
 d=pd.DataFrame([dict(minor=m,codigo='CIP044',nombre_asignatura='Trabajo en equipo'),
                 dict(minor=m,codigo='DFI044',nombre_asignatura='Curso distinto')])
 blocked,issues=equivalence_conflicts(d)
 assert 'CIP044' in blocked[m] and len(issues)==1
 assert canonical_code('CIP044',blocked[m])=='CIP044'

def test_formation_general_special_rule_and_department():
 assert unit_eligibility('COORDINACION DE FORMACIÓN GENERAL E IDIOMAS')=='SI'
 assert unit_eligibility('DEPARTAMENTO DE ADMINISTRACION Y ECONOMIA')=='NO'
 assert unit_eligibility('Unidad desconocida')=='REVISAR'

def test_name_order_and_fixed_width_truncation():
 assert names_compatible(['PEREZ GONZALEZ ANA MARIA','GONZALEZ PEREZ ANA MARIA'])
 full='PEREZ GONZALEZ MARIA FERNANDA ALEJANDRITA ISABEL'
 assert names_compatible([full[:40],full])
 assert not names_compatible(['MARIA PEREZ','MARIA GONZALEZ'])
