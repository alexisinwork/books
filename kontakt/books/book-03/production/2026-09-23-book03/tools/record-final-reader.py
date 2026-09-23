"""Record the coordinator's actual complete final preview inspection and mirror artifacts."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;phase=run/'terra-final-v1';base=phase/'assembled'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
source=base/'manuscript.md';render=read(base/'reader/render/render-check.json');check=read(base/'reader/docx-check.json');docx=list((base/'reader').glob('*.docx'));assert len(docx)==1
assert render['pages']==64 and len(render['contact_sheets'])==11 and render['text_matches_docx_ignoring_layout_whitespace']
assert all(not p['blank'] and p['out_of_bounds']==0 and p['words']>=55 for p in render['page_checks'])
assert check['source_sha256']==sha(source) and check['docx_sha256']==sha(docx[0]) and check['extraction_matches_markdown_content']
out=base/'visual-review.json';assert not out.exists()
write(out,{'status':'final_reader_complete_actual_visual_review','source_sha256':sha(source),'docx_sha256':sha(docx[0]),'pdf_sha256':render['pdf_sha256'],'pages':64,'actual_visual_coverage':'Coordinator viewed all11 current contact sheets, every page1-64, after final v4 layout adjustment.','observations':['No blank page, clipped text, damaged character or isolated one-paragraph chapter tail found in current preview.','Consistent headings, paragraph structure and readable body; chapter-ending whitespace is retained where natural.','CH14 uses an explicit break before a complete final reaction, avoiding a19-word tail without compressing body spacing further.'],'format_history':'Initial71-page preview had a blank58 and short tails.67- and64-page intermediate layouts preserved. Current64-page layout passed a new text comparison and complete visual inspection.','text_identity':'All formatting passes asserted identical decoded DOCX paragraph text; current DOCX extraction and PDF text match source ignoring layout markup/whitespace.','renderer':'docx-preview/Chromium, not native Word','contact_sheets':[dict(x,sha256=sha(base/'reader/render'/x['path'])) for x in render['contact_sheets']]})
check.update(render='complete_actual_visual_review_all64_pages',render_report='render/render-check.json',visual_review='../visual-review.json');write(base/'reader/docx-check.json',check)
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
files=[Path(__file__).resolve(),*[p for p in phase.rglob('*') if p.is_file()],*run.glob('final-*.json')]
for f in files:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d);assert sha(f)==sha(d)
print(json.dumps({'pages':64,'contacts_actually_viewed':11,'source_sha256':sha(source),'files_mirrored':len(files)}))
