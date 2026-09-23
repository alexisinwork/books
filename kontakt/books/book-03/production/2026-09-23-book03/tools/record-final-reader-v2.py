"""Validate visual coverage by unchanged page bytes and actual viewing of the changed page."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;phase=run/'terra-final-v2';base=phase/'assembled'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
source=base/'manuscript.md';render=read(base/'reader/render/render-check.json');check=read(base/'reader/docx-check.json');docx=list((base/'reader').glob('*.docx'));assert len(docx)==1
comparison=read(base/'page-image-comparison.json');assert len(comparison['items'])==64
assert [x['page'] for x in comparison['items'] if not x['same_rendered_bytes']]==['page-57.png']
assert render['pages']==64 and render['text_matches_docx_ignoring_layout_whitespace'] and all(not p['blank'] and p['out_of_bounds']==0 and p['words']>=55 for p in render['page_checks'])
assert check['source_sha256']==sha(source) and check['docx_sha256']==sha(docx[0]) and check['extraction_matches_markdown_content']
for item in comparison['items']:
 assert sha(base/'reader/render'/item['page'])==item['sha256']
 if item['same_rendered_bytes']:assert sha(run/'terra-final-v1/assembled/reader/render'/item['page'])==item['sha256']
out=base/'visual-review.json';assert not out.exists()
write(out,{'status':'final_reader_complete_visual_coverage','source_sha256':sha(source),'docx_sha256':sha(docx[0]),'pdf_sha256':render['pdf_sha256'],'pages':64,'actual_visual_coverage':'Fresh viewing of current page57 at full page scale; other63current PNG pages byte-identical to the prior complete64-page visual inspection, validated individually. No claim of64fresh separate views after one-word change.','previous_visual_review_sha256':comparison['previous_visual_review_sha256'],'page_identity_evidence':'page-image-comparison.json','observations':['Current page57 has clear subject at the repaired paragraph, readable text and normal margins.','All64pages have supported visual coverage; no blank page, clipped text or isolated one-paragraph chapter tail found.','Layout from validated v1 retained; fresh source extraction and current PDF text comparison passed.'],'renderer':'docx-preview/Chromium, not native Word'})
check.update(render='complete_visual_coverage_all64_pages',visual_review='../visual-review.json',render_report='render/render-check.json');write(base/'reader/docx-check.json',check)
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [Path(__file__).resolve(),*[p for p in phase.rglob('*') if p.is_file()],*run.glob('final-v2-*.json')]:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d);assert sha(f)==sha(d)
print(json.dumps({'pages':64,'freshly_viewed_changed_page':57,'verified_identical_prior_views':63,'source_sha256':sha(source)}))
