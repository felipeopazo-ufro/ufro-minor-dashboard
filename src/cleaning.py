import re, unicodedata
import pandas as pd
MINORS = ['Minor en Inglés','Minor en Emprendimiento','Minor en Relaciones Interculturales']
TRONCALES = {MINORS[0]:['DFI183','DFI185'], MINORS[1]:['DFI165','IAE145'], MINORS[2]:['DFI300','DFI310']}
HISTORICAL_EQUIVALENCES = {f'CIP{n}':f'DFI{n}' for n in ('040','044','101','105','140','147','159','163','165','171','183','185')}
def text(v): return '' if v is None or pd.isna(v) else str(v).strip()
def norm(v): return ' '.join(''.join(c for c in unicodedata.normalize('NFD',text(v).upper()) if unicodedata.category(c)!='Mn').split())
def matricula(v): return re.sub(r'\.0$','',re.sub(r'\s+','',text(v)).upper())
def minor(v):
    for term,m in [('INGLES',MINORS[0]),('EMPRENDIMIENTO',MINORS[1]),('INTERCULTURALES',MINORS[2])]:
        if term in norm(v):return m
    return ''
def code(v):return re.sub(r'[\s-]+','',norm(v))
def canonical_code(v,blocked=()):
    c=code(v)
    return c if c in blocked else HISTORICAL_EQUIVALENCES.get(c,c)
def names_compatible(values):
    names={norm(v) for v in values if norm(v)}
    if len({tuple(sorted(n.split())) for n in names})<=1:return True
    shortest=min(names,key=len)
    # The institutional master has some names cut at precisely 40 characters.
    return len(shortest)==40 and all(n.startswith(shortest) for n in names)
