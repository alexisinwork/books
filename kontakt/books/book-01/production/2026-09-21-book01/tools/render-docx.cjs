// Actual DOCX preview in Chromium; not native Microsoft Word pagination.
const fs = require('fs');
const path = require('path');
const deps = 'C:/Users/alexi/AppData/Local/Temp/kontakt-docx-render-20260921/node_modules';
const {chromium} = require(path.join(deps, 'playwright-core'));
(async () => {
  const [source, output] = process.argv.slice(2);
  fs.mkdirSync(output, {recursive:true});
  const browser = await chromium.launch({executablePath:'C:/Users/alexi/AppData/Local/Google/Chrome SxS/Application/chrome.exe', headless:true});
  try {
    const page = await browser.newPage();
    await page.setContent('<!doctype html><html><head><meta charset="utf-8"></head><body><div id="document"></div></body></html>');
    await page.addScriptTag({path:path.join(deps,'jszip/dist/jszip.min.js')});
    await page.addScriptTag({path:path.join(deps,'docx-preview/dist/docx-preview.min.js')});
    await page.evaluate(async (base64) => {
      const bytes=Uint8Array.from(atob(base64), c=>c.charCodeAt(0));
      await docx.renderAsync(bytes.buffer, document.getElementById('document'), null, {inWrapper:true, ignoreLastRenderedPageBreak:false, renderHeaders:true, renderFooters:true});
      await document.fonts.ready;
    }, fs.readFileSync(source).toString('base64'));
    await page.addStyleTag({content:'@page {size:A4; margin:20mm 23mm} @media print {body{margin:0}.docx-wrapper{background:white!important;padding:0!important}.docx-wrapper>section.docx{box-shadow:none!important;margin:0!important;padding:0!important;min-height:0!important;height:auto!important;width:auto!important;break-after:auto!important} .docx-wrapper article{width:auto!important} p{orphans:2;widows:2}}'});
    fs.writeFileSync(path.join(output,'preview-text.txt'),await page.locator('#document').innerText(),'utf8');
    await page.pdf({path:path.join(output,'preview.pdf'),printBackground:true,preferCSSPageSize:true});
    fs.writeFileSync(path.join(output,'renderer.json'),JSON.stringify({renderer:'docx-preview in Chromium',browser:await browser.version(),docx_preview:require(path.join(deps,'docx-preview/package.json')).version,scope:'Actual DOCX parsed and rendered; preview pagination, not native Word/LibreOffice.'},null,2));
  } finally {await browser.close();}
})();
