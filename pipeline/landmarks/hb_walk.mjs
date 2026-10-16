// Walk tests for the HB models in the test server (port 5176). Start points / headings in the HB frame (d along tracks, c across).
import { chromium } from '/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs';
const A = (-21 * Math.PI) / 180, ORG = [1760, -650];
const W = (d, c) => [ORG[0] + d * Math.cos(A) - c * Math.sin(A), ORG[1] + d * Math.sin(A) + c * Math.cos(A)];
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
p.on('pageerror', (e) => { if (!/arc/.test(e.message)) console.log('pageerror', e.message.slice(0, 120)); });
const s0 = W(48, -95);
await p.goto(`http://127.0.0.1:5176/?at=${s0[0]},${s0[1]},0&t=12:00&nopost`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
await p.evaluate(() => { const S = (window.__w = { s: [], ok: 1 }); setInterval(() => { const q = window.sbxPlayer; S.s.push({ x: q.x, y: q.y, z: q.z, v: q.speed }); }, 100); });
const fr = (x, y) => { const dx = x - ORG[0], dy = y - ORG[1]; return [dx * Math.cos(A) + dy * Math.sin(A), -dx * Math.sin(A) + dy * Math.cos(A)]; };
async function run(name, from, to, secs) {
  for (let attempt = 0; attempt < 4; attempt++) {
    try { await run1(name, from, to, secs); return; } catch (e) { console.log('retry', attempt, String(e).slice(0, 80)); await p.goto(`http://127.0.0.1:5176/?at=${W(...from)[0]},${W(...from)[1]},0&t=12:00&nopost`); await p.waitForFunction(() => window.sbxReady, null, { timeout: 120000 }); }
  }
}
async function run1(name, from, to, secs) {
  const f = W(...from), t = W(...to);
  await p.waitForFunction(() => window.sbxReady && window.sbxPlayer, null, { timeout: 120000 });
  await p.evaluate(() => { if (!window.__w || !window.__w.ok) { window.__w = null; }
    if (!window.__w) { const S = (window.__w = { s: [], ok: 1 }); setInterval(() => { const q = window.sbxPlayer; if (q) S.s.push({ x: q.x, y: q.y, z: q.z, v: q.speed }); }, 100); } });
  await p.evaluate(async ([f]) => { await window.sbxTiles.update(f[0], f[1]); }, [f]);
  await p.waitForTimeout(2500);
  // find the yaw whose motion points at the target
  let best = null;
  for (let k = 0; k < 16; k++) {
    const yaw = (k * Math.PI) / 8;
    await p.evaluate(([f, yaw]) => { window.sbxPlayer.teleport(f[0], f[1], yaw); window.__w.s.length = 0; }, [f, yaw]);
    await p.keyboard.down('KeyW'); await p.waitForTimeout(350); await p.keyboard.up('KeyW');
    const e = await p.evaluate(() => { const q = window.sbxPlayer; return [q.x, q.y]; });
    const dx = e[0] - f[0], dy = e[1] - f[1], ux = t[0] - f[0], uy = t[1] - f[1];
    const cos = (dx * ux + dy * uy) / (Math.hypot(dx, dy) * Math.hypot(ux, uy) + 1e-9);
    if (!best || cos > best.cos) best = { yaw, cos };
  }
  await p.evaluate(([f, yaw]) => { window.sbxPlayer.teleport(f[0], f[1], yaw); window.__w.s.length = 0; }, [f, best.yaw]);
  await p.waitForTimeout(300);
  await p.keyboard.down('Shift'); await p.keyboard.down('KeyW'); await p.waitForTimeout(secs * 1000); await p.keyboard.up('KeyW'); await p.keyboard.up('Shift');
  const r = await p.evaluate(() => { const s = window.__w.s; if (!s.length) return { n: 0, last: { x: 0, y: 0 }, minz: 0, maxz: 0, pts: [] }; return { n: s.length, last: s[s.length - 1], minz: Math.min(...s.map((a) => a.z)), maxz: Math.max(...s.map((a) => a.z)), pts: s.filter((_, i) => i % 15 === 0).map((a) => [+a.x.toFixed(1), +a.y.toFixed(1), +a.z.toFixed(2)]) }; });
  const end = fr(r.last.x, r.last.y);
  console.log(`${name}: yawfit ${best.cos.toFixed(2)} start dc ${from} -> end dc [${end.map((v) => v.toFixed(1))}] z ${r.minz.toFixed(2)}..${r.maxz.toFixed(2)} (target ${to})`);
  console.log('   path dc:', r.pts.map((a) => fr(a[0], a[1]).map((v) => +v.toFixed(0)).join(',') + '@' + a[2]).join('  '));
}
await run('C hall -> Querhalle -> platform 10/11', [30, -5], [-120, -5], 26);
await run('D hall east exit', [80, -4], [135, -4], 12);
await run('F kiosk collision (kiosk at d=18, c=-10)', [30, -10], [5, -10], 8);
await run('G hall south wall (c=-25) blocked', [70, -8], [70, -60], 8);
await b.close();
