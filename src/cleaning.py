import re, unicodedata
import pandas as pd
MINORS = ['Minor en Inglés','Minor en Emprendimiento','Minor en Relaciones Interculturales']
TRONCALES = {MINORS[0]:['DFI183','DFI185'], MINORS[1]:['DFI165','IAE145'], MINORS[2]:['DFI300','DFI310']}
def text(v): return '' if v is None or pd.isna(v) else str(v).strip()
def norm(v): return ' '.join(''.join(c for c in unicodedata.normalize('NFD',text(v).upper()) if unicodedata.category(c)!='Mn').split())
def matricula(v): return re.sub(r'\.0$','',re.sub(r'\s+','',text(v)).upper())
def minor(v):
    for term,m in [('INGLES',MINORS[0]),('EMPRENDIMIENTO',MINORS[1]),('INTERCULTURALES',MINORS[2])]:
        if term in norm(v):return m
    return ''
def code(v):return re.sub(r'[\s-]+','',norm(v))
