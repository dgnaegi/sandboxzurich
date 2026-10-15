import { chromium } from '/Users/danielgnagi/gtazurich/web/node_modules/playwright/index.mjs';
const [,, out, ...qs] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message)); p.on('console', (m) => { if (m.type() === 'error' || m.type()==='warning') console.log(m.text().slice(0,200)); });
await p.goto('http://localhost:5173/lmtest.html?' + qs.join('&'));
await p.waitForFunction(() => window.done, null, { timeout: 30000 });
await p.screenshot({ path: out }); await b.close();
