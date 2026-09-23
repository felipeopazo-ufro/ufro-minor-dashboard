import pandas as pd
from .cleaning import norm

def reconcile(result,old):
    new=result['enrollments'];h=result['history'];rows=[]
    for (mat,m,s),g in old.groupby(['matricula','minor','semester_enrolled'],dropna=False):
        n=new[(new.matricula==mat)&(new.minor==m)&(new.semester_enrolled==s)]
        codes=set(g.codigo); types=g.groupby('tipo').codigo.nunique().to_dict()
        states=sorted(set(g.old_status)); grads=sorted(set(g.graduation_semester)-{''})
        row=dict(matricula=mat,minor=m,inscripcion_anterior=s,estado_anterior=' / '.join(states),egreso_anterior=' / '.join(grads),asignaturas_anterior=len(codes),troncales_anterior=types.get('Troncal',0),electivas_anterior=types.get('Electiva',0))
        if n.empty:
            candidate=new[new.matricula==mat]
            row.update(coincidencia='Sólo seguimiento anterior',inscripciones_nuevas=' / '.join(sorted(candidate.semester_enrolled.unique())),minors_nuevos=' / '.join(sorted(candidate.minor.unique())))
        else:
            r=n.iloc[0];selected=set(h.loc[(h.enrollment_id==r.enrollment_id)&h.counted_for_completion,'codigo'])
            old_state={'EGRESADO/A':'EGRESADO','CURSANDO':'CURSANDO','ELIMINADO/A':'ELIMINADO'}.get(norm(row['estado_anterior']),row['estado_anterior'])
            new_state='ELIMINADO' if r.status.startswith('ELIMINADO') else r.status
            row.update(coincidencia='Ambos',estado_nuevo=r.status,egreso_nuevo=r.graduation_semester,asignaturas_nuevas=r.total_completed,troncales_nuevas=r.troncales_completed,electivas_nuevas=r.electives_completed,diferencia_estado=old_state!=new_state,diferencia_egreso=row['egreso_anterior']!=r.graduation_semester,diferencia_asignaturas=codes!=selected,codigos_solo_anterior=', '.join(sorted(codes-selected)),codigos_solo_nuevo=', '.join(sorted(selected-codes)))
        rows.append(row)
    comparison=pd.DataFrame(rows)
    keys=set(zip(old.matricula,old.minor,old.semester_enrolled))
    only=new[[tuple(x) not in keys for x in new[['matricula','minor','semester_enrolled']].values]]
    both=comparison[comparison.coincidencia=='Ambos']
    summary=pd.DataFrame({'Indicador':['Participaciones nuevas','Participaciones históricas','Coincidencias de participación','Sólo nueva base','Sólo seguimiento anterior','Diferencias de estado','Diferencias de asignaturas','Diferencias de egreso'],'Cantidad':[len(new),len(comparison),len(both),len(only),len(comparison)-len(both),int(both.diferencia_estado.sum()),int(both.diferencia_asignaturas.sum()),int(both.diferencia_egreso.sum())]})
    return {'Resumen':summary,'Coincidencias':both,'Discrepancias estado':both[both.diferencia_estado==True],'Discrepancias asignaturas':both[both.diferencia_asignaturas==True],'Discrepancias egreso':both[both.diferencia_egreso==True],'Solo nueva base':only,'Solo seguimiento anterior':comparison[comparison.coincidencia!='Ambos']}
