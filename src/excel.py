"""Small OOXML export for the deployed Python app; strings never become formulas."""
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED
from xml.sax.saxutils import escape,quoteattr
import math,re

def col(n):
    out=''
    while n:n,k=divmod(n-1,26);out=chr(65+k)+out
    return out

def clean(v):return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',str(v))
def excel_bytes(tables):
    buf=BytesIO();ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main';rel='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    with ZipFile(buf,'w',ZIP_DEFLATED) as z:
        sheets=[];rels=[];overrides=[]
        for i,(name,df) in enumerate(tables.items(),1):
            name=re.sub(r'[\[\]:*?/\\]',' ',name)[:31]
            sheets.append(f'<sheet name={quoteattr(name)} sheetId="{i}" r:id="rId{i}"/>');rels.append(f'<Relationship Id="rId{i}" Type="{rel}/worksheet" Target="worksheets/sheet{i}.xml"/>');overrides.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
            values=[list(df.columns)]+df.astype(object).where(df.notna(),None).values.tolist();n=max(1,len(df.columns));body=[]
            for ri,row in enumerate(values,1):
                cells=[]
                for ci,v in enumerate(row,1):
                    pos=f'{col(ci)}{ri}';style=1 if ri==1 else (2 if str(df.columns[ci-1]).lower()=='nota' else 0)
                    if v is None:continue
                    if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v):cells.append(f'<c r="{pos}" s="{style}" t="n"><v>{v}</v></c>')
                    else:cells.append(f'<c r="{pos}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{escape(clean(v))}</t></is></c>')
                body.append(f'<row r="{ri}" ht="{32 if ri==1 else 20}" customHeight="1">'+''.join(cells)+'</row>')
            widths=''.join(f'<col min="{j}" max="{j}" width="{min(55,max(18,len(str(c))+3))}" customWidth="1"/>' for j,c in enumerate(df.columns,1))
            xml=f'<worksheet xmlns="{ns}"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols>{widths}</cols><sheetData>{"".join(body)}</sheetData><autoFilter ref="A1:{col(n)}{len(values)}"/></worksheet>'
            z.writestr(f'xl/worksheets/sheet{i}.xml',xml)
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}" xmlns:r="{rel}"><sheets>{"".join(sheets)}</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels',f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{"".join(rels)}<Relationship Id="styles" Type="{rel}/styles" Target="styles.xml"/></Relationships>')
        z.writestr('_rels/.rels',f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="{rel}/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/styles.xml',f'<styleSheet xmlns="{ns}"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF17365D"/></patternFill></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1"/></xf><xf numFmtId="2" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
        z.writestr('[Content_Types].xml',f'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>{"".join(overrides)}</Types>')
    return buf.getvalue()
