from pathlib import Path
from src.data_loader import load_cip

def test_historical_cip_workbook_uses_filename_for_course_and_term():
    path=Path('/workspace/scratch/eeb1818071f2/project_sources/07-Consolidado-Asignaturas-CIP-troncales.xlsx')
    if not path.exists():return
    grades=load_cip(path.read_bytes())
    assert len(grades)==207
    assert set(grades.codigo)=={'CIP165','CIP183','CIP185'}
    assert set(grades.canonical_course_code)=={'DFI165','DFI183','DFI185'}
    row=grades[grades.source_file=='CIP165 2015-2.xls'].iloc[0]
    assert row.semester=='2015-2' and row.codigo=='CIP165'
    assert row.source_file=='CIP165 2015-2.xls'
