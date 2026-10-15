// Ground look: 4 points x day/night x desktop/phone -> preview/_ground_<tag>_*.png ; sheet via sheet.py
import { chromium, devices } from 'playwright';
const tag = process.argv[2] ?? 'a';
const OUT = new URL('../../preview/', import.meta.url).pathname;
const P = { lang: '785,-635,0.37', helv: '760,-905,-0.3', mil: '1013,-606,-0.94', baeck: '505,-715,0.3' };
const VP = { d: { viewport: { width: 1000, height: 560 } }, p: { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true } };
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
for (const [vn, v] of Object.entries(VP)) {
  const pg = await (await b.newContext(v)).newPage();
  pg.on('pageerror', (e) => console.log('pageerror', e.message));
  for (const [pn, at] of Object.entries(P)) for (const [tn, t] of [['day', '12:00'], ['night', '22:30']]) {
    await pg.goto(`http://localhost:5173/?at=${at}&t=${t}`);
    await pg.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
    await pg.waitForTimeout(5000);
    await pg.screenshot({ path: `${OUT}_ground_${tag}_${vn}_${pn}_${tn}.png` });
  }
}
await b.close();
