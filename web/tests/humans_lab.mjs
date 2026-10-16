// node tests/humans_lab.mjs out.jpg "ids" zoom [night]  -> render of npc figures in the lab page (no game needed)
import { chromium } from 'playwright';
const [out, ids = '0,1,2,3,4,5,6,7', zoom = 'full', night = '', extra = ''] = process.argv.slice(2);
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await b.newPage({ viewport: { width: 1600, height: 450 } });
p.on('pageerror', (e) => console.log('pageerror', e.message)); p.on('console', (m) => { if (m.type() === 'error') console.log('ERR', m.text()); });
await p.goto(`http://localhost:5173/tests/humans_lab.html?ids=${ids}&zoom=${zoom}${night ? '&night' : ''}${extra}`);
await p.waitForFunction(() => window.done, null, { timeout: 90000 });
await p.screenshot({ path: out, type: 'jpeg', quality: 85 }); await b.close();
