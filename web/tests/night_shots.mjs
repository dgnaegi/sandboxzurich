// Night look: 5 points at 22:30, desktop + phone -> ../preview/_night_<tag>_<vp>_<pt>.png ; sheet via sheet.py
import { chromium, devices } from 'playwright';
const tag = process.argv[2] ?? 'a';
const OUT = new URL('../../preview/', import.meta.url).pathname;
const P = { lang: '785,-635,0.37', helv: '785,-885,2.53', hohl: '-345,-70,-2.4', roent: '738,111,1.16', baeck: '505,-690,0.36' };
const VP = { d: { viewport: { width: 1000, height: 560 } }, p: { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true } };
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
for (const [vn, v] of Object.entries(VP)) {
  const pg = await (await b.newContext(v)).newPage();
  pg.on('pageerror', (e) => console.log('pageerror', e.message));
  for (const [pn, at] of Object.entries(P)) {
    await pg.goto(`http://localhost:5173/?at=${at}&t=22:30`);
    await pg.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
    await pg.waitForTimeout(5000);
    await pg.screenshot({ path: `${OUT}_night_${tag}_${vn}_${pn}.png` });
  }
}
await b.close();
