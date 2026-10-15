import { chromium } from '/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs';
const [,, out, at, t] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
await p.goto('http://localhost:5173/?at=' + at + '&t=' + (t || '12:00'));
await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
await p.waitForTimeout(6000);
await p.screenshot({ path: out }); await b.close();
