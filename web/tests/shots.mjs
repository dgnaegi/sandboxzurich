// Screenshots at fixed camera points in desktop and phone viewports, plus a contact sheet.
// Usage: (cd web && npm run dev) in background, then: cd web && npm run shots [baseUrl]
import { chromium, devices } from 'playwright';
import { mkdirSync, readFileSync } from 'node:fs';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const OUT = new URL('../../preview/', import.meta.url).pathname;
const ONLY = process.env.ONLY?.split(',');
const POINTS = {
  helvetiaplatz: '760,-905,-0.3&t=10:30',
  langstrasse: '785,-635,0.37&t=17:40',
  abend: '785,-635,0.37&t=19:05',
  nacht: '785,-635,0.37&t=22:30',
  militaerstrasse: '1013,-606,-0.94&t=13:00',
  wiese: '700,-930,0.5&t=14:00',
  flohmarkt: '676,-935,3.3&t=10:00&day=5',
  criticalmass: '790,-625,3.5&t=18:33&day=4',
  demo: '868,-430,3.5&t=14:24&day=5',
  rosaluxemburg: '-1463,458,-0.40&t=11:00',
  altstetten: '-2086,790,0&t=12:30',
  wiedikon: '436,-1320,0&t=18:10',
  karte: '785,-635,0.37&map',
};
const VIEWPORTS = {
  desktop: { viewport: { width: 1280, height: 720 } },
  phone: { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true },
};

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const files = [];
for (const [vp, opts] of Object.entries(VIEWPORTS)) {
  const ctx = await browser.newContext(opts);
  const page = await ctx.newPage();
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  for (const [name, at] of Object.entries(POINTS).filter(([n]) => !ONLY || ONLY.includes(n))) {
    await page.goto(`${BASE}/?at=${at}`);
    await page.waitForFunction(() => window.gtaReady, null, { timeout: 60000 });
    await page.waitForTimeout(2500);
    const f = `${OUT}${name}_${vp}.png`;
    await page.screenshot({ path: f });
    console.log(name, vp, await page.textContent('#stats'));
    files.push(f);
  }
  await ctx.close();
}
// contact sheet
const page = await (await browser.newContext({ viewport: { width: 1600, height: 900 } })).newPage();
const imgs = files.map((f) => `<img src="data:image/png;base64,${readFileSync(f).toString('base64')}" style="width:530px;margin:2px">`).join('');
await page.setContent(`<body style="margin:0;background:#222">${imgs}</body>`);
await page.waitForTimeout(500);
await page.screenshot({ path: `${OUT}contact.png`, fullPage: true });
await browser.close();
