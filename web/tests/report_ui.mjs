// QA: «Fehler melden» page (ui/report.ts). PC + phone landscape/portrait: page opens from the menu, context block shows
// place/position/build, GitHub link carries template, label, title, body with position, deep link and the typed text;
// typing P/M in the box keeps the menu open and the map closed; Escape leaves the box first,
// the second Escape closes the menu. Screenshots -> preview/report_ui_<vp>.jpg. Usage: node tests/report_ui.mjs [base]
import { launch, open, OUT } from './qa_lib.mjs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const b = await launch();
let fails = 0;
const check = (name, ok, extra = '') => { console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${extra ? '  ' + extra : ''}`); if (!ok) fails++; };
const shown = (page, id) => page.evaluate((id) => getComputedStyle(document.getElementById(id)).display !== 'none', id);
for (const vp of ['pc', 'phoneL', 'phoneP']) {
  const { ctx, page, log } = await open(b, vp, `${BASE}/?at=789,-873,0.3&t=12:00&nohelp&nopost`);
  await page.waitForTimeout(2500);   // HUD place name updates every 30 frames (slow headless GL)
  await page.click('#btn-menu'); await page.waitForTimeout(300);
  await page.click('#m-report'); await page.waitForTimeout(300);
  const info = await page.evaluate(() => document.getElementById('r-info')?.textContent ?? '');
  check(`${vp} context block`, /Ort:/.test(info) && /Build:/.test(info) && /at=789\.0,-873\.0/.test(info), info.split('\n')[0]);
  await page.fill('#r-text', 'Test: Auto verschwunden');
  await page.focus('#r-text');
  await page.keyboard.type(' pm');   // P would close the menu, M would open the map
  check(`${vp} typing p/m keeps menu, no map`, (await shown(page, 'menu')) && !(await shown(page, 'bigmap')));
  const u = new URL(await page.getAttribute('#r-github', 'href'));
  check(`${vp} github url`, u.hostname === 'github.com' && u.pathname === '/dgnaegi/sandboxzurich/issues/new' && u.searchParams.get('template') === 'bug_report.md' && u.searchParams.get('labels') === 'bug' && /^Fehler: /.test(u.searchParams.get('title') ?? ''), u.searchParams.get('title'));
  const body = u.searchParams.get('body') ?? '';
  check(`${vp} body: text, position, deep link`, body.includes('Auto verschwunden pm') && /x 789\.0, y -873\.0/.test(body) && /\?at=789\.0,-873\.0,0\.30,/.test(body) && /Build:/.test(body), `${u.href.length} chars`);
  await page.keyboard.press('Escape'); await page.waitForTimeout(150);
  check(`${vp} Escape leaves the box, menu stays`, (await shown(page, 'menu')) && (await page.evaluate(() => document.activeElement?.id !== 'r-text')));
  await page.screenshot({ path: `${OUT}report_ui_${vp}.jpg`, type: 'jpeg', quality: 60 });
  await page.keyboard.press('Escape'); await page.waitForTimeout(150);
  check(`${vp} second Escape closes the menu`, !(await shown(page, 'menu')));
  const errs = log.errors.filter((e) => !/cloudflareinsights|net::ERR_FAILED/.test(e));   // analytics beacon has no CORS for localhost
  check(`${vp} no page errors`, errs.length === 0, errs.slice(0, 2).join(' | '));
  await ctx.close();
}
await b.close();
console.log(fails ? `REPORT_UI FAIL ${fails}` : 'REPORT_UI OK');
process.exit(fails ? 1 : 0);
