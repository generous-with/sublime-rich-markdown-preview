const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright');

(async () => {
  const root = path.resolve(__dirname, '..');
  const browser = await chromium.launch({headless:true, ...(process.env.CHROMIUM_EXECUTABLE ? {executablePath:process.env.CHROMIUM_EXECUTABLE} : {})});
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(pathToFileURL(path.join(root,'web','preview.html')).href);
    const baseUri = pathToFileURL(path.join(root,'examples')).href + '/';
    const markdown = fs.readFileSync(path.join(root,'examples','sample.md'),'utf8');
    await page.evaluate(payload => window.updatePreview(payload), {markdown,baseUri});
    await page.waitForSelector('.mermaid svg');
    await page.waitForFunction(() => document.images.length > 0 && [...document.images].every(i => i.complete && i.naturalWidth > 0));
    assert.equal(await page.locator('h1').count(),1);
    assert.equal(await page.locator('table').count(),1);
    assert.ok(await page.locator('.hljs-keyword').count() > 0);
    assert.equal(await page.locator('input[type=checkbox]:checked').count(),1);
    assert.ok(Number(await page.locator('strong').first().evaluate(e => getComputedStyle(e).fontWeight)) >= 600);
    const selection = await page.evaluate(() => {const range=document.createRange();range.selectNodeContents(document.querySelector('strong'));const s=getSelection();s.removeAllRanges();s.addRange(range);return s.toString();});
    assert.equal(selection,'真正的粗体');
    await page.evaluate(payload=>window.updatePreview(payload), {markdown:markdown+'\nUNSAVEDLIVECHANGE\n',baseUri});
    assert.ok((await page.locator('#content').innerText()).includes('UNSAVEDLIVECHANGE'));
    await page.evaluate(payload=>window.updatePreview(payload), {markdown:'# Test\n\n<script>window.unsafe=1</script><img src=x onerror="window.unsafe=2"><iframe src="https://example.com"></iframe>',baseUri});
    assert.equal(await page.locator('#content script, #content iframe, #content [onerror]').count(),0);
    assert.equal(await page.evaluate(()=>window.unsafe),undefined);
    assert.equal(await page.evaluate(()=>DOMPurify.version),'3.4.17');
    assert.deepEqual(errors,[]);
    console.log('Renderer: rich formatting, local image, Mermaid, selection, live updates and sanitization passed.');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
