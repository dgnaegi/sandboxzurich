import { launch, open, OUT, touch } from './qa_lib.mjs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const tag = process.argv[3] ?? 'local';
const b = await launch();
for (const vp of ['phoneP', 'phoneL', 'pc']) {
  const { ctx, page, log, cdp } = await open(b, vp, BASE + '/', { wait: false });
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${OUT}qa_review_boot_${tag}_${vp}_0loading.jpg`, quality: 60, type: 'jpeg' });
  const ld = await page.evaluate(() => ({ title: document.getElementById('ld-title')?.textContent, msg: document.getElementById('ld-msg')?.textContent, vis: getComputedStyle(document.getElementById('loading')).display }));
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 180000 });
  const loadMs = Date.now() - 0;
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${OUT}qa_review_boot_${tag}_${vp}_1start.jpg`, quality: 60, type: 'jpeg' });
  const info = await page.evaluate(() => ({
    help: document.getElementById('help')?.innerText.slice(0, 400), helpVis: getComputedStyle(document.getElementById('help')).display,
    prompt: document.getElementById('prompt')?.innerText, place: document.getElementById('place-name')?.innerText,
    hud: document.getElementById('hud')?.innerText.replace(/\n/g, ' | ').slice(0, 200),
    menuBtn: document.getElementById('btn-menu') && getComputedStyle(document.getElementById('btn-menu')).display,
    pos: [window.sbxPlayer.x, window.sbxPlayer.y],
  }));
  console.log(vp, tag, JSON.stringify({ ld, ...info }));
  console.log('  errors', log.errors.length, log.errors.slice(0, 5), 'bad', log.bad.slice(0, 8), 'warns', log.warns.length, log.warns.slice(0, 3));
  await ctx.close();
}
await b.close();
