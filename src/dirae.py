import pandas as pd
COLUMNS=['Matrícula','Nombre','Año-semestre inscripción','Año-semestre asignatura','Nota','Código_asig','Nombre Asignatura','Programa Minor','Tipo Asignatura']
def dirae_tables(result,selected=None):
    e=result['enrollments'] if selected is None else selected
    pending=e[(e.status=='EGRESADO')&~e.get('dirae_ready',~e.requires_review)].copy()
    e=e[(e.status=='EGRESADO')&~e.requires_review&e.get('dirae_ready',True)]
    h=result['history'];rows=[]
    for r in e.to_dict('records'):
        g=h[(h.enrollment_id==r['enrollment_id'])&h.counted_for_completion]
        if len(g)!=5 or sum(g.course_type=='Troncal')!=2 or sum(g.course_type=='Electiva')!=3:raise ValueError('La selección DIRAE no cumple 2 troncales y 3 electivas.')
        for a in g.to_dict('records'):rows.append([r['matricula'],r['nombre'],r['semester_enrolled'],a['semester'],a['nota'],a['codigo'],a['nombre_asignatura'],r['minor'],a['course_type']])
    return {'DIRAE':pd.DataFrame(rows,columns=COLUMNS),'RESUMEN ESTUDIANTES':e,'EGRESADOS POR RESPALDAR':pending,'VALIDACIONES':result['quality']}
