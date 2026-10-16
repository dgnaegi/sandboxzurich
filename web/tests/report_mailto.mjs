// "Stimmt etwas nicht?" button must produce a mailto: URL with coordinate, direction, time, tile (pc + phone viewport).
import { chromium, devices } from 'playwright';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
let bad = 0;
for (const [vp, opts] of [['pc', { viewport: { width: 1280, height: 720 } }], ['phone', { ...devices['iPhone 13'], viewport: { width: 844, height: 390 } }]]) {
  const p = await (await b.newContext(opts)).newPage();
  p.on('pageerror', (e) => console.log('pageerror', e.message));
  await p.goto(`${BASE}/?at=785,-635,0.37&t=17:40`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await p.evaluate(() => document.getElementById('btn-menu').click());
  await p.evaluate(() => document.getElementById('m-report').click());
  const url = await p.evaluate(() => window.sbxLastReportUrl);
  const body = decodeURIComponent(url?.split('body=')[1] ?? ''), subj = decodeURIComponent(url?.match(/subject=([^&]*)/)?.[1] ?? '');
  const ok = url?.startsWith('mailto:daniel.gnaegi@protonmail.com?') && subj === 'Sandbox Zürich – Korrektur' && /x=78\d\.\d y=-6\d\d\.\d/.test(body) && /WGS84: 47\.\d{6}, 8\.\d{6}/.test(body)
    && /Blickrichtung: /.test(body) && /Spielzeit: .* 17:/.test(body) && /Kachel: t_\d+_-?\d+/.test(body) && body.includes('Was stimmt nicht? Foto gern anhängen');
  console.log(vp, ok ? 'ok' : 'FAIL'); if (!ok) { bad++; console.log(url); }
  if (vp === 'pc') console.log(body);
}
await b.close(); process.exit(bad ? 1 : 0);
