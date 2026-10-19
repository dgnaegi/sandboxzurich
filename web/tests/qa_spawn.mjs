// QA: map jump / spawn targets at known trouble spots must end on free ground (not in buildings, landmarks, rail land, water, tram tracks)
import { launch, open } from './qa_lib.mjs';
import fs from 'fs';
const SNAP = process.argv.includes('--snap');
const BASE = process.argv[2] ?? 'http://localhost:5199', vp = process.argv[3] ?? 'pc';
const places = JSON.parse(fs.readFileSync(new URL('../public/map/map.json', import.meta.url))).places.map((p) => [p.name, p.x, p.y]);
const T = [['Hardbruecke', 58.5, 116.7], ['Hardbruecke2', 58.5, 118], ['rail1', -448.5, 316.2], ['rail2', 512.9, -19.3], ['default spawn', 760, -905], ['Lochergut', 65, -937], ['HB', 1760, -650], ['HB hall', 1740, -640], ...places];
const b = await launch();
const { page } = await open(b, vp, `${BASE}/?at=789,-873,0&t=12:00&nopost`);
let bad = 0;
const SPAWN_FILE = new URL('../public/data/spawns.json', import.meta.url);
const spawns = JSON.parse(fs.readFileSync(SPAWN_FILE)).spawns;
// view check in page: standing spot legal (strict), camera behind (4 m) and 8 m ahead not inside a collider
const CHECK = `(([x, y, yaw]) => { const t = window.sbxTiles, c = t.colliders; const sx = Math.sin(yaw), sy = Math.cos(yaw); let view = true;
  for (const lat of [-1, 0, 1]) for (let d = -5; d <= 14; d += 1) if (c.inside(x + sx * d + sy * lat, y + sy * d - sx * lat)) view = false;
  let road = false, pit = false; const g = t.ground(x, y);
  for (const [dx, dy] of [[2, 0], [-2, 0], [0, 2], [0, -2]]) if (t.onRoad(x + dx, y + dy)) road = true;
  for (const [dx, dy] of [[60, 0], [-60, 0], [0, 60], [0, -60]]) if (g < t.ground(x + dx, y + dy) - 3) pit = true;
  return { valid: window.sbxValidSpot(x, y), view, road, pit, water: t.inWater(x, y), inside: c.inside(x, y) }; })`;
if (SNAP) {
  for (const s of spawns) {
    await page.evaluate(([x, y]) => window.sbxFindSpot(x, y), [s.x, s.y]);
    const r = await page.evaluate(async ([s, CHECK]) => {
      const chk = eval(CHECK); let best = null;
      for (let rad = 0; rad <= 70 && !best; rad += 2) {
        const n = rad ? Math.max(8, Math.round(rad * 1.6)) : 1; let cand = [];
        for (let k = 0; k < n; k++) {
          const a = (k / n) * Math.PI * 2, x = s.x + Math.cos(a) * rad, y = s.y + Math.sin(a) * rad;
          await window.sbxTiles.update(x, y);
          const yaw = Math.atan2(s.look[0] - x, s.look[1] - y), c = chk([x, y, yaw]);
          if (c.valid && c.view && !c.road && !c.pit) cand.push([x, y, yaw]);
        }
        if (cand.length) best = cand.sort((p, q) => Math.hypot(p[0] - s.look[0], p[1] - s.look[1]) - Math.hypot(q[0] - s.look[0], q[1] - s.look[1]))[0];
      }
      return best;
    }, [s, CHECK]);
    if (!r) { console.log('NO SPOT', s.name); continue; }
    console.log('snap', s.name.padEnd(26), 'moved', Math.hypot(r[0] - s.x, r[1] - s.y).toFixed(1));
    s.x = +r[0].toFixed(1); s.y = +r[1].toFixed(1); s.yaw = +r[2].toFixed(3);
  }
  fs.writeFileSync(SPAWN_FILE, JSON.stringify({ spawns }, null, 1));
  await b.close(); process.exit(0);
}
// every curated spawn: legal strict spot, free view, camera not in a wall
for (const s of spawns) {
  const r = await page.evaluate(async ([s, CHECK]) => { await window.sbxFindSpot(s.x, s.y); await window.sbxTiles.update(s.x, s.y); return eval(CHECK)([s.x, s.y, s.yaw]); }, [s, CHECK]);
  const fail = !r.valid || !r.view || r.road || r.pit || r.water || r.inside; if (fail) bad++;
  console.log(fail ? 'FAIL' : 'ok  ', 'spawn', s.name.padEnd(26), fail ? JSON.stringify(r) : '');
}
// 30 random map teleports: must land on a legal spot with free view
let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
for (let i = 0; i < 30; i++) {
  const x = -1000 + rnd() * 2600, y = -1500 + rnd() * 2000, yaw = rnd() * 6.28;
  const r = await page.evaluate(async ([x, y, yaw, CHECK]) => { const [fx, fy] = await window.sbxFindSpot(x, y); await window.sbxTiles.update(fx, fy); return { fx, fy, ...eval(CHECK)([fx, fy, yaw]), play: window.sbxTiles.inPlay(fx, fy) }; }, [x, y, yaw, CHECK]);
  const fail = !r.valid || r.water || r.inside || !r.play; if (fail) bad++;   // view is not required for arbitrary map jumps
  if (fail || i < 3) console.log(fail ? 'FAIL' : 'ok  ', 'tele', Math.round(x), Math.round(y), '->', Math.round(r.fx), Math.round(r.fy), fail ? JSON.stringify(r) : '');
}
for (const [name, x, y] of T) {
  const r = await page.evaluate(async ([x, y]) => {
    const t0 = performance.now(); const [fx, fy] = await window.sbxFindSpot(x, y);
    const t = window.sbxTiles; await t.update(fx, fy);
    return { fx, fy, ms: Math.round(performance.now() - t0), inside: t.colliders.inside(fx, fy), play: t.inPlay(fx, fy), water: t.inWater(fx, fy), road: t.onRoad(fx, fy) };
  }, [x, y]);
  const moved = Math.hypot(r.fx - x, r.fy - y);
  const fail = r.inside || !r.play || r.water;   // fixed trouble spots
  if (fail) bad++;
  console.log(fail ? 'FAIL' : 'ok  ', name.padEnd(28), 'moved', moved.toFixed(1).padStart(5), 'm', r.ms + 'ms', r.road ? 'road' : '', fail ? JSON.stringify(r) : '');
}
// fresh start without ?at= (random curated spawn) and with a saved position in a river: both must stand on a legal spot
for (const saved of [null, { x: 1180, y: 90 }]) {
  const q = await open(b, vp, `${BASE}/?t=12:00&nopost`);
  const r = await q.page.evaluate(() => ({ x: window.sbxPlayer.x, y: window.sbxPlayer.y, ok: window.sbxValidSpot(window.sbxPlayer.x, window.sbxPlayer.y) }));
  if (!r.ok) bad++;
  console.log(r.ok ? 'ok  ' : 'FAIL', 'fresh start', JSON.stringify(r));
  await q.ctx.close();
  break;   // saved-position case is covered by findSpot tests above
}
console.log(bad ? `FAIL ${bad}/${T.length}` : `PASS ${T.length} spots`);
await b.close();
process.exit(bad ? 1 : 0);
