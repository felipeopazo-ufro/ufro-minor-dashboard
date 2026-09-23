import re

def ordinal(value):
    m = re.fullmatch(r'(\d{4})[-/ ]([12])', str(value).strip())
    if not m or not 1900 <= int(m[1]) <= 2200: raise ValueError(f'Semestre inválido: {value}')
    return int(m[1])*2+int(m[2])-1

def semester(index): return f'{index//2}-{index%2+1}'
def normalize(value): return semester(ordinal(value))
def add(value, amount): return semester(ordinal(value)+amount)
