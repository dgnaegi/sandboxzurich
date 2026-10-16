// velotunnel: put the player at the south portal, walk in, print z; screenshot preview/velotunnel.jpg. node velotunnel_walk.mjs [port]
import { chromium } from '/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs';
import fs from 'fs';
const port = process.argv[2] || '5199';
const ovr = JSON.parse(fs.readFileSync('/Users/danielgnagi/sandboxzurich/pipeline/overrides/landmarks_velotunnel.json')).landmarks;
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: 640, height: 360 } })).newPage();
await p.route('**/data/landmarks.json', async (r) => { const j = await (await r.fetch()).json(); j.landmarks.push(...ovr); await r.fulfill({ json: j }); });
const t = [0.565, 0.825], s0 = [1470.5 + t[0] * 4, -724.8 + t[1] * 4];
p.on('console', (m) => { if (/landmark|velotunnel/i.test(m.text())) console.log('C:', m.text().slice(0, 200)); });
p.on('response', (r) => { if (/velotunnel/.test(r.url())) console.log('R:', r.status(), r.url()); });
await p.goto(`http://127.0.0.1:${port}/?at=${s0[0]},${s0[1]}&t=12:00`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
await p.waitForTimeout(6000);
const yaw = Math.atan2(t[0], t[1]);
await p.evaluate(([x, y, yaw]) => window.sbxPlayer.teleport(x, y, yaw), [s0[0], s0[1], yaw]);
await p.waitForTimeout(800);
await p.keyboard.down('w'); await p.keyboard.down('Shift');
const out = [];
for (let i = 0; i < 14; i++) { await p.waitForTimeout(1000); out.push(await p.evaluate(() => { const q = window.sbxPlayer; return `${q.x.toFixed(0)},${q.y.toFixed(0)}:z${q.z.toFixed(1)}`; })); if (i === 11) await p.screenshot({ path: '/Users/danielgnagi/sandboxzurich/preview/velotunnel.jpg', type: 'jpeg', quality: 80 }); }
await p.keyboard.up('w'); await p.keyboard.up('Shift');
console.log(out.join(' | '));
await b.close();
