#!/usr/bin/env python3
"""Check the rendered PDF against the DOCX and prepare bounded visual review."""
from pathlib import Path
import hashlib
import json
import re
import fitz
from docx import Document
from PIL import Image, ImageDraw

REV=Path(__file__).resolve().parent
OUT=REV/'audit/render'
pdf=next(OUT.glob('*.pdf'))
docx=next(REV.glob('*.docx'))
document=fitz.open(pdf)
normal=lambda s: re.sub(r'\s+','',s)
expected=normal('\n'.join(p.text for p in Document(docx).paragraphs))
actual=normal('\n'.join(p.get_text(sort=True) for p in document))
assert actual==expected, 'Rendered PDF text differs from the complete DOCX text'
headings=[]
stats=[]
for i,page in enumerate(document):
    text=page.get_text()
    headings.extend((int(m[1]),i+1) for m in re.finditer(r'Глава\s+(\d+)\.',text))
    outside=[w[:5] for w in page.get_text('words') if w[0]<-1 or w[1]<-1 or w[2]>page.rect.width+1 or w[3]>page.rect.height+1]
    stats.append(dict(page=i+1,chars=len(text.strip()),outside=outside))
starts=dict(headings)
selected={1,len(document)}
for n in [13,14,24,32]:
    selected.update(range(starts[n]-1,starts[n+1]+1))
selected.update(i+1 for i,p in enumerate(document) if 'цепочкапометок' in normal(p.get_text(sort=True)))
selected=sorted(selected)
contact=OUT/'contact-sheets'
contact.mkdir(exist_ok=True)
for base in range(0,len(selected),9):
    pages=selected[base:base+9]
    cw,ch=460,690
    sheet=Image.new('RGB',(cw*3,ch*3),'#b8b8b8')
    draw=ImageDraw.Draw(sheet)
    for j,num in enumerate(pages):
        pix=document[num-1].get_pixmap(matrix=fitz.Matrix(1.15,1.15),alpha=False)
        im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        im.thumbnail((cw-12,ch-36))
        x=(j%3)*cw+6;y=(j//3)*ch+30
        sheet.paste(im,(x,y));draw.text((x,y-24),f'Page {num}',fill='black')
    sheet.save(contact/f'selected-{base//9+1:02d}.jpg',quality=90)
for needle,name in [('Мелкие строки плыли','fatigue'),('Над головой загремели','hatch'),('пальцем от левой колонки','manos'),('То есть заплатить','garm')]:
    i=next(i for i,p in enumerate(document) if normal(needle) in normal(p.get_text()))
    document[i].get_pixmap(matrix=fitz.Matrix(2,2)).save(OUT/f'{name}.png')
result=dict(pdf=pdf.name,pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
    docx_sha256=hashlib.sha256(docx.read_bytes()).hexdigest(),
    renderer='LibreOffice 26.2.6.3; Georgia and Courier New from /mnt/c/Windows/Fonts via private FONTCONFIG_FILE',
    fonts=sorted(set(f[3] for p in document for f in p.get_fonts())),pages=len(document),headings=headings,
    pdf_docx_text_comparison='passed; page text sorted by layout coordinates, whitespace normalized',blank_pages=[s['page'] for s in stats if not s['chars']],
    outside_text_pages=[s['page'] for s in stats if s['outside']],visual_review_pages=selected,
    visual_review_status='pending',mechanical_page_stats=stats)
(OUT/'render-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(OUT/'pages.json').write_text(json.dumps(dict(pages=len(document),headings=headings),ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['mechanical_page_stats','headings']},ensure_ascii=False))
