// QA: «Fehler melden» page (ui/report.ts). PC + phone landscape/portrait: page opens from the menu, context block shows
// place/position/build; «Absenden» with an empty box asks for text and sends nothing; with text it posts title/body
// (position, deep link, typed text) to /api/report (mocked here) and shows the issue number with a link, box cleared;
// a 503 from the Worker shows the reason plus the pre-filled GitHub link as fallback and keeps the text; the GitHub link
// itself carries template, label, title and body; typing P/M in the box keeps the menu open and the map closed; Escape
// leaves the box first, the second Escape closes the menu. Screenshots -> preview/report_ui_<vp>.jpg.
// Usage: node tests/report_ui.mjs [base]
import { launch, open, OUT } from './qa_lib.mjs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const ISSUE = 'https://github.com/dgnaegi/sandboxzurich/issues/42';
const b = await launch();
let fails = 0;
const check = (name, ok, extra = '') => { console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${extra ? '  ' + extra : ''}`); if (!ok) fails++; };
const shown = (page, id) => page.evaluate((id) => getComputedStyle(document.getElementById(id)).display !== 'none', id);
const status = (page) => page.evaluate(() => document.getElementById('r-status')?.textContent ?? '');
const statusLink = (page) => page.evaluate(() => document.querySelector('#r-status a')?.getAttribute('href') ?? '');
const until = (page, re) => page.waitForFunction((s) => new RegExp(s).test(document.getElementById('r-status')?.textContent ?? ''), re.source, { timeout: 4000 }).then(() => true, () => false);
for (const vp of ['pc', 'phoneL', 'phoneP']) {
  const { ctx, page, log } = await open(b, vp, `${BASE}/?at=789,-873,0.3&t=12:00&nohelp&nopost`);
  // the Worker is not part of the Vite dev server: answer /api/report here, first like a created issue, later like a Worker without token
  const posted = [];
  let answer = { status: 201, body: { url: ISSUE, number: 42 } };
  await page.route('**/api/report', (route) => { posted.push(JSON.parse(route.request().postData() ?? 'null')); route.fulfill({ status: answer.status, contentType: 'application/json', body: JSON.stringify(answer.body) }); });
  await page.waitForTimeout(2500);   // HUD place name updates every 30 frames (slow headless GL)
  await page.click('#btn-menu'); await page.waitForTimeout(300);
  await page.click('#m-report'); await page.waitForTimeout(300);
  const info = await page.evaluate(() => document.getElementById('r-info')?.textContent ?? '');
  check(`${vp} context block`, /Ort:/.test(info) && /Build:/.test(info) && /at=789\.0,-873\.0/.test(info), info.split('\n')[0]);
  await page.click('#r-send'); await page.waitForTimeout(200);
  check(`${vp} empty box: asks for text, nothing sent`, /beschreiben/.test(await status(page)) && posted.length === 0, await status(page));
  await page.fill('#r-text', 'Test: Auto verschwunden');
  await page.focus('#r-text');
  await page.keyboard.type(' pm');   // P would close the menu, M would open the map
  check(`${vp} typing p/m keeps menu, no map`, (await shown(page, 'menu')) && !(await shown(page, 'bigmap')));
  const u = new URL(await page.getAttribute('#r-github', 'href'));
  check(`${vp} github fallback url`, u.hostname === 'github.com' && u.pathname === '/dgnaegi/sandboxzurich/issues/new' && u.searchParams.get('template') === 'bug_report.md' && u.searchParams.get('labels') === 'bug' && /^Fehler: /.test(u.searchParams.get('title') ?? ''), u.searchParams.get('title'));
  const body = u.searchParams.get('body') ?? '';
  check(`${vp} fallback body: text, position, deep link`, body.includes('Auto verschwunden pm') && /x 789\.0, y -873\.0/.test(body) && /\?at=789\.0,-873\.0,0\.30,/.test(body) && /Build:/.test(body), `${u.href.length} chars`);
  await page.click('#r-send');
  const ok = await until(page, /#42/);
  const sent = posted[0] ?? {};
  check(`${vp} send: posts title/body, shows #42 with link, clears box`, ok && posted.length === 1 && /^Fehler: /.test(sent.title ?? '') && (sent.body ?? '').includes('Auto verschwunden pm') && /x 789\.0, y -873\.0/.test(sent.body ?? '') && (await statusLink(page)) === ISSUE && (await page.inputValue('#r-text')) === '', await status(page));
  check(`${vp} send: json only title/body`, Object.keys(sent).sort().join() === 'body,title' && !/\*\*Ort:\*\*[^\n]*unbekannt/.test(sent.body ?? ''));
  answer = { status: 503, body: { error: 'unavailable' } };
  await page.fill('#r-text', 'Zweiter Versuch');
  await page.click('#r-send');
  const failed = await until(page, /nicht geklappt/);
  check(`${vp} worker 503: reason, GitHub fallback link, text kept`, failed && /nicht eingerichtet/.test(await status(page)) && (await statusLink(page)).startsWith('https://github.com/dgnaegi/sandboxzurich/issues/new?') && /Zweiter%20Versuch/.test(await statusLink(page)) && (await page.inputValue('#r-text')) === 'Zweiter Versuch', await status(page));
  await page.focus('#r-text');
  await page.keyboard.press('Escape'); await page.waitForTimeout(150);
  check(`${vp} Escape leaves the box, menu stays`, (await shown(page, 'menu')) && (await page.evaluate(() => document.activeElement?.id !== 'r-text')));
  await page.screenshot({ path: `${OUT}report_ui_${vp}.jpg`, type: 'jpeg', quality: 60 });
  await page.keyboard.press('Escape'); await page.waitForTimeout(150);
  check(`${vp} second Escape closes the menu`, !(await shown(page, 'menu')));
  // analytics beacon has no CORS for localhost; the 503 is the mocked Worker answer above (Chromium logs every failed resource)
  const errs = log.errors.filter((e) => !/cloudflareinsights|net::ERR_FAILED|status of 503/.test(e));
  check(`${vp} no page errors`, errs.length === 0, errs.slice(0, 2).join(' | '));
  await ctx.close();
}
await b.close();
console.log(fails ? `REPORT_UI FAIL ${fails}` : 'REPORT_UI OK');
process.exit(fails ? 1 : 0);
