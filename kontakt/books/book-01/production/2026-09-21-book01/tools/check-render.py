"""Check DOCX-preview PDF text, page bounds, and generate every page for inspection."""
from pathlib import Path
import sys, json, hashlib, unicodedata
sys.path.insert(0,'C:/Users/alexi/AppData/Local/Temp/kontakt-docx-render-20260921/python')
import pymupdf as fitz

import argparse
p=argparse.ArgumentParser(); p.add_argument('--draft',type=Path,required=True); args=p.parse_args(); base=args.draft.resolve()
out=base/'reader/render'
pdf=out/'preview.pdf'
doc=fitz.open(pdf)
def norm(t):return ''.join(c for c in unicodedata.normalize('NFKC',t) if not c.isspace() and c!='\u00ad')
expected=(base/'reader/docx-extracted.txt').read_text(encoding='utf-8')
extracted='\n'.join(p.get_text() for p in doc)
(out/'pdf-extracted.txt').write_bytes(extracted.encode('utf-8'))
stats=[]
sheet=fitz.open(); composite=sheet.new_page(width=620,height=((len(doc)+1)//2)*445)
for i,p in enumerate(doc):
    pix=p.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
    pix.save(out/f'page-{i+1:02d}.png')
    x=(i%2)*310; y=(i//2)*445
    composite.insert_image(fitz.Rect(x+5,y+5,x+300,y+422),stream=pix.tobytes('png'))
    composite.insert_text((x+12,y+435),f'Page {i+1}',fontsize=10)
    words=p.get_text('words')
    outside=[w for w in words if w[0]<-1 or w[1]<-1 or w[2]>p.rect.width+1 or w[3]>p.rect.height+1]
    stats.append({'page':i+1,'words':len(words),'out_of_bounds':len(outside),'blank':not bool(words)})
composite.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False).save(out/'contact.png')
report={'renderer':'docx-preview/Chromium; not native Word','pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'pages':len(doc),'text_matches_docx_ignoring_layout_whitespace':norm(expected)==norm(extracted),'page_checks':stats,'visual_review':'pending'}
(out/'render-check.json').write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
assert report['text_matches_docx_ignoring_layout_whitespace'],'PDF text differs; inspect extraction'
assert all(not p['out_of_bounds'] and not p['blank'] for p in stats),stats
print(json.dumps(report,ensure_ascii=False))
