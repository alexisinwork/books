#!/usr/bin/env python3
"""Verify the selected release, bind actual inspection evidence and copy four DOCX."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

BASE=Path(__file__).resolve().parent
RELEASE=BASE/'release-05'
DESKTOP=Path('/mnt/c/Users/alexi/Desktop')
DEST=DESKTOP/'Оповідання — українська фінальна редакція — 2026-09-14'
sys.path.insert(0,str(BASE/'tools'))
import revise_docx_text as edit
from docx import Document

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:
        f.write(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def main():
    assert not DEST.exists(), 'Never overwrite an author folder'
    result=subprocess.run([sys.executable,str(BASE/'test_release_tools.py'),'-v'],capture_output=True,text=True)
    save(RELEASE/'tool-tests.txt',result.stdout+result.stderr)
    assert result.returncode==0
    now=datetime.now(timezone.utc).isoformat()
    config=read(BASE/'config.json')['stories']
    catalog=read(RELEASE/'release.json')
    inspections=[]
    source_locations=[]
    for item,evidence in zip(config,catalog['stories']):
        assert item['id']==evidence['story']
        story=BASE/'stories'/item['id']
        meta=RELEASE/item['id']
        docx=RELEASE/evidence['docx']
        final=meta/'final.uk.txt'
        assert sha(docx)==evidence['docx_sha256']
        assert sha(final)==evidence['text_sha256']==sha(story/'uk.txt')
        values=[p.text for p in edit.body_paragraphs(Document(docx)) if p.text.strip()]
        assert values==[edit.plain(v) for v in edit.read_projection(final)]
        assert len(values)==evidence['paragraphs']
        manifest=read(story/'input-manifest.json')
        for source in manifest['inputs']:
            assert sha(story/source['snapshot'])==source['sha256']
            if source['role'] not in ('ru','uk'):
                continue
            current=Path(source['origin'])
            note=None
            if not current.exists() and item['id']=='random-experiment' and source['role']=='uk':
                current=DESKTOP/'Sol/Випадковий експеримент.docx'
                note='Renamed by author during work; same source hash.'
            assert current.exists() and sha(current)==source['sha256'], f'Author source changed: {current}'
            source_locations.append({'story':item['id'],'role':source['role'],
                                     'recorded_origin':source['origin'],'current_origin':str(current),
                                     'sha256':sha(current),'note':note})
        rv=read(meta/'render/verification.json')
        assert rv['docx_sha256']==sha(docx)
        assert sha(meta/'render'/rv['pdf'])==rv['pdf_sha256']
        assert rv['pdf_text_exact_ignoring_layout_whitespace']
        assert not any(p['blank'] or p['out_of_page_bounds'] for p in rv['page_checks'])
        visual={'docx_sha256':sha(docx),'pdf_sha256':rv['pdf_sha256'],
                'method':'Actual model visual inspection of contact sheets for all pages; explicit full-size samples. This is not a human typesetter signoff.',
                'result':'Readable Ukrainian; no clipping, accidental blank pages or broken font substitution found.',
                'contacts':[],'full_size_samples':[]}
        for name in rv['contacts']:
            current=meta/'render'/name
            prior=BASE/'release-04'/item['id']/'render'/name
            direct=item['id']=='space-is-no-place-for-the-living' and name=='contact-017-030.png'
            if not direct:
                assert sha(current)==sha(prior), 'Require new image inspection'
            visual['contacts'].append({'file':name,'sha256':sha(current),
                 'inspection':'directly inspected release-05 image' if direct else 'byte-identical to directly inspected release-04 image'})
        samples={'random-experiment':[1,4],'history':[1,20],
                 'space-is-no-place-for-the-living':[30],'where-ducks-fly-in-winter':[1,30]}[item['id']]
        for page in samples:
            image=meta/'render'/f'page-{page:03d}.png'
            if item['id']=='random-experiment' and page==1:
                assert sha(image)==sha(BASE/'release-04'/item['id']/'render'/image.name)
            visual['full_size_samples'].append({'file':image.name,'sha256':sha(image)})
        save(meta/'visual-review.json',visual)
        inspections.append({'story':item['id'],'docx_sha256':sha(docx),'text_sha256':sha(final),
                            'paragraphs':len(values),'rendered_pages':rv['pages'],'visual_evidence':str((meta/'visual-review.json').relative_to(RELEASE))})
    invocations=[]
    for path in sorted(BASE.glob('stories/*/reviews-*/**/invocation.json')):
        record=read(path)
        assert record['client']=='agy' and record['role']!='opus'
        assert sha(path.parent/'prompt.txt')==record['prompt_sha256']
        if record.get('report_sha256'):
            assert sha(path.parent/'REPORT.md')==record['report_sha256']
        invocations.append({'file':str(path.relative_to(BASE)),'invocation_sha256':sha(path),
                            'status':record['status'],'role':record['role'],
                            'target_sha256':record['target_sha256'], 'report_sha256':record.get('report_sha256')})
    save(RELEASE/'review-index.json',{'scope_interpretation':'../RECONCILIATION.md','invocations':invocations})
    save(RELEASE/'source-locations-at-delivery.json',source_locations)
    gate={'status':'editorial_complete_for_author_reading','created_utc':now,
          'release':'release-05','stories':inspections,'total_body_paragraphs':sum(x['paragraphs'] for x in inspections),
          'opus':'waived by current author request; not run','gemini_route':'agy CLI only',
          'all_external_models_passed':False,
          'limits':['History repeat Flash checks refused by provider; final delta checked by editor.',
                    'Some target-only structural/scientific preferences deliberately not applied; see reconciliation.',
                    'Source ambiguity retained; no human native-reader or scientific-certification claim.'],
          'reconciliation_sha256':sha(BASE/'RECONCILIATION.md'),
          'issues_sha256':sha(BASE/'audit/issues.json'),
          'mechanics':'7 tool regression tests passed; full body XML and rendered PDF text agree; source DOCX unchanged.',
          'publication_canon_promoted':False,'earlier_releases':'01–04 superseded; retained for traceability'}
    save(RELEASE/'final-gate.json',gate)
    DEST.mkdir(exist_ok=False)
    copied=[]
    for evidence in catalog['stories']:
        source=RELEASE/evidence['docx']
        target=DEST/source.name
        assert not target.exists()
        shutil.copy2(source,target)
        assert sha(source)==sha(target)
        copied.append({'title':evidence['title'],'repository_file':str(source.relative_to(BASE)),
                       'desktop_file':str(target),'sha256':sha(target)})
    assert sorted(p.name for p in DEST.iterdir())==sorted(Path(x['desktop_file']).name for x in copied)
    save(BASE/'delivery.json',{'status':'copied_and_verified','created_utc':now,'folder':str(DEST),
                             'files':copied,'final_gate':'release-05/final-gate.json',
                             'source_originals_preserved':True,'github_delivery':'recorded separately after push'})
    print(json.dumps({'delivery':str(DEST),'files':len(copied),'body_paragraphs':gate['total_body_paragraphs']},ensure_ascii=False))

if __name__=='__main__':
    main()
