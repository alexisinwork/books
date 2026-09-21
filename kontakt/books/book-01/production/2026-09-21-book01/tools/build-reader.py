"""Build a reading copy of this draft and retain exact paragraph anchors."""
from pathlib import Path
import hashlib, json, re
from docx import Document
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

import argparse
p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,required=True); p.add_argument('--chapter',type=int,required=True); args=p.parse_args()
source=args.source.resolve(); base=source.parent
chapter=args.chapter
text = source.read_text(encoding='utf-8')
blocks = text.rstrip('\n').split('\n\n')
sha = hashlib.sha256(source.read_bytes()).hexdigest()
reader = base / 'reader'
reader.mkdir(exist_ok=True)
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2)
sec.left_margin = sec.right_margin = Cm(2.3)
normal = doc.styles['Normal']
normal.font.name, normal.font.size = 'Georgia', Pt(11)
normal.paragraph_format.line_spacing = 1.2
normal.paragraph_format.space_after = Pt(4)
normal.paragraph_format.widow_control = True
lang = OxmlElement('w:lang'); lang.set(qn('w:val'), 'uk-UA')
normal.element.get_or_add_rPr().append(lang)
anchors, expected = [], []
for i, block in enumerate(blocks, 1):
    heading = block.startswith('#')
    clean = re.sub(r'^#+\s+', '', block)
    quoted = clean.startswith('> ')
    if quoted: clean = re.sub(r'^>\s?', '', clean, flags=re.M)
    p = doc.add_paragraph(style='Heading 1' if heading else 'Normal')
    if quoted:
        p.paragraph_format.left_indent = Cm(.6)
        p.paragraph_format.right_indent = Cm(.6)
    for j, part in enumerate(re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*)', clean)):
        run = p.add_run(part.strip('*') if part.startswith('*') else part)
        if quoted: run.italic = True
        if part.startswith('**'): run.bold = True
        elif part.startswith('*') and part.endswith('*') and len(part)>2: run.italic = True
    if clean in ['***', '* * *', '— — —']:
        p.text = '* * *'; p.alignment = 1
    expected.append(p.text)
    anchors.append({'id':f'P{i:04d}', 'source_sha256':sha, 'text':block, 'docx_paragraph':i})
doc.core_properties.title = f'Контакт — глава {chapter} — чернетка'
doc.core_properties.subject = 'Український оригінал; робоча версія для читання автором'
doc.core_properties.author = 'Sol — робоча чернетка'
dest = reader / f'Контакт — глава {chapter} — чернетка.docx'
doc.save(dest)
actual = [p.text for p in Document(dest).paragraphs]
assert actual == expected
(base/'anchors.json').write_bytes((json.dumps({'source':source.name,'source_sha256':sha,'paragraphs':anchors},ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
(reader/'docx-extracted.txt').write_bytes(('\n\n'.join(actual)+'\n').encode('utf-8'))
(reader/'docx-check.json').write_bytes((json.dumps({'source_sha256':sha,'docx_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'paragraphs':len(actual),'extraction_matches_markdown_content':True,'format':'A4, Georgia 11pt, 1.2 spacing, Ukrainian language','render':'pending'},indent=2)+'\n').encode('utf-8'))
print(json.dumps({'docx':str(dest),'paragraphs':len(actual),'sha256':sha},ensure_ascii=False))
