import pandas as pd
import pytest
from src.official import apply_official,load_official,count
from src.dirae import dirae_tables
from src.cleaning import MINORS
from src.configuration import validate_exceptions
from test_rules import calc,complete,enrollment

def result(status='ELIMINADO POR PLAZO',review=False):
 e=calc(complete());h=pd.DataFrame(e.pop('history'));e.update(status=status,requires_review=review)
 return {'enrollments':pd.DataFrame([e]),'quality':pd.DataFrame(columns=['nivel','tipo','matricula','detalle','fuente','fila_origen']),'history':h}
def official(total=5,removed='',resigned='',state='Alumno UFRO',mat='001'):
 return pd.DataFrame([dict(matricula=mat,official_total=total,official_cores=2 if total==5 else 0,official_electives=3 if total==5 else total,official_elimination_date=removed,official_resignation_date=resigned,official_completion_date='',official_enrollment_date='',official_certificate_date='',official_student_state=state)])

def test_official_completion_overrides_deadline():
 r=apply_official(result(),official());e=r['enrollments'].iloc[0]
 assert e.status=='EGRESADO' and e.calculated_status=='ELIMINADO POR PLAZO' and not e.dirae_ready
 assert dirae_tables(r)['DIRAE'].empty
 assert len(dirae_tables(r)['EGRESADOS POR RESPALDAR'])==1

def test_matching_completion_export():
    r=apply_official(result('EGRESADO'),official());assert len(dirae_tables(r)['DIRAE'])==5

def test_official_five_of_five_does_not_authorize_two_semester_extension():
    e=calc(complete(s='2027-2'),now='2027-2');h=pd.DataFrame(e.pop('history'))
    actual=apply_official({'enrollments':pd.DataFrame([e]),'history':h,'quality':pd.DataFrame()},official())['enrollments'].iloc[0]
    assert actual.status=='REQUIERE REVISIÓN' and not actual.dirae_ready

def test_official_five_of_five_does_not_erase_failed_core():
    from test_rules import grade
    e=calc([grade('DFI183','2024-1',False)]+complete(s='2027-1'),now='2027-1')
    h=pd.DataFrame(e.pop('history'))
    actual=apply_official({'enrollments':pd.DataFrame([e]),'history':h,'quality':pd.DataFrame()},official())['enrollments'].iloc[0]
    assert actual.status=='ELIMINADO POR TRONCAL'

def test_individual_academic_reconciliation_overrides_only_documented_four_of_five():
    e=calc(complete(s='2027-1'),now='2027-1');h=pd.DataFrame(e.pop('history'))
    r={'enrollments':pd.DataFrame([e]),'history':h,'quality':pd.DataFrame()}
    adjudication=[dict(matricula='001',minor=MINORS[0],decision='ACADEMIC_5_OF_5_ONE_SEMESTER_LATE')]
    actual=apply_official(r,official(total=4),adjudication)['enrollments'].iloc[0]
    assert actual.status=='EGRESADO' and actual.probable_exceptionality
    assert actual.official_total==4 and actual.total_completed==5
    assert actual.status_reason=='5/5 académico comprobado; un semestre después del plazo ordinario. Avance histórico registraba 4/5.'

def test_individual_academic_reconciliation_does_not_bypass_a_four_of_five_academic_result():
    e=calc(complete(s='2026-2')[:-1],now='2027-1');h=pd.DataFrame(e.pop('history'))
    actual=apply_official({'enrollments':pd.DataFrame([e]),'history':h,'quality':pd.DataFrame()},official(total=4),
        [dict(matricula='001',minor=MINORS[0],decision='ACADEMIC_5_OF_5_ONE_SEMESTER_LATE')])['enrollments'].iloc[0]
    assert actual.status=='REQUIERE REVISIÓN' and not actual.probable_exceptionality
    assert 'No cumple las 3 electivas válidas requeridas' in actual.status_reason

def test_official_partial_blocks_calculated_complete():
 e=apply_official(result('EGRESADO'),official(4))['enrollments'].iloc[0]
 assert e.status=='REQUIERE REVISIÓN' and not e.dirae_ready and e.graduation_semester==''

def test_official_removal():assert apply_official(result(),official(0,removed='2026-01-01'))['enrollments'].iloc[0].status=='ELIMINADO OFICIAL'
def test_official_resignation():assert apply_official(result(),official(0,resigned='2026-01-01'))['enrollments'].iloc[0].status=='RENUNCIA OFICIAL'
def test_conflicting_official():assert apply_official(result(),official(removed='2026-01-01'))['enrollments'].iloc[0].requires_review

def test_unmatched_not_added():
 r=apply_official(result(),official(mat='002'));assert len(r['enrollments'])==1 and len(r['official_unmatched'])==1

def test_multiple_enrollments_not_assigned():
 r=result();r['enrollments']=pd.concat([r['enrollments'],r['enrollments']],ignore_index=True)
 r=apply_official(r,official());assert not r['enrollments'].official_linked.any() and len(r['official_unmatched'])==1

def test_unknown_deadline_not_final():assert apply_official(result())['enrollments'].iloc[0].status=='PLAZO EXCEDIDO POR REVISAR'
def test_no_official_does_not_remove_enrollment():assert apply_official(result('CURSANDO'))['enrollments'].iloc[0].status=='CURSANDO'
def test_current_pause_does_not_invent_semester():
 e=apply_official(result('CURSANDO'),official(0,state='Alumno con postergación de Estudios'))['enrollments'].iloc[0]
 assert e.status=='PAUSA ACADÉMICA REGISTRADA' and e.deadline_semester=='2026-2'
def test_completed_pause_keeps_completion():assert apply_official(result('EGRESADO'),official(state='Alumno con Retiro Temporal'))['enrollments'].iloc[0].status=='EGRESADO'

@pytest.mark.parametrize('text,n',[('5 de 5',5),('5/5',5),('0 de 5',0)])
def test_total(text,n):assert count(text,5)==n
@pytest.mark.parametrize('text',['6/5','5/6','5','n/a',''])
def test_invalid_total(text):
 with pytest.raises(ValueError):count(text,5)

def test_extraordinary_extension():
 ex={'matricula':'001','minor':MINORS[0],'enrollment_id':'','semestre_afectado':'2026-2','tipo_excepcion':'Prórroga extraordinaria','observacion':'Autorización sintética','contabiliza_en_plazo':'SI','aprobada':'SI','semestres_extension':'1'}
 r=calc([],ex=[ex]);assert r['deadline_semester']=='2027-1' and r['extra_semesters']==1
 assert calc([],ex=[ex,ex])['extra_semesters']==1
 ex['aprobada']='NO';assert calc([],ex=[ex])['deadline_semester']=='2026-2'

def test_extraordinary_missing_amount_rejected():
 e=enrollment();e['enrollment_id']='001|'+MINORS[0]+'|2024-1'
 row=dict(matricula='001',minor=MINORS[0],enrollment_id='',semestre_afectado='2026-2',tipo_excepcion='Prórroga extraordinaria',observacion='Respaldo',contabiliza_en_plazo='SI',aprobada='SI')
 with pytest.raises(ValueError,match='semestres_extension'):validate_exceptions(pd.DataFrame([row]).to_csv(index=False).encode(),pd.DataFrame([e]))

def test_real_official_snapshot():
 from pathlib import Path
 from src.storage import unpack
 from src.official import OFFICIAL_FILE
 p=Path('data/private/minor_snapshot.zip')
 if not p.exists():pytest.skip('Paquete real privado no distribuido con el código')
 files=unpack(p.read_bytes())
 if OFFICIAL_FILE not in files:pytest.skip('Paquete anterior sin fuente oficial')
 d=load_official(files[OFFICIAL_FILE])
 assert len(d)==653 and sum(d.official_total==5)==351
 assert sum(d.official_elimination_date!='')==17
