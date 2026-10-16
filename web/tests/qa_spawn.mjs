// QA: map jump / spawn targets at known trouble spots must end on free ground (not in buildings, landmarks, rail land, water, tram tracks)
import { launch, open } from './qa_lib.mjs';
import fs from 'fs';
const BASE = process.argv[2] ?? 'http://localhost:5199', vp = process.argv[3] ?? 'pc';
const places = JSON.parse(fs.readFileSync(new URL('../public/map/map.json', import.meta.url))).places.map((p) => [p.name, p.x, p.y]);
const T = [['Hardbruecke', 58.5, 116.7], ['Hardbruecke2', 58.5, 118], ['rail1', -448.5, 316.2], ['rail2', 512.9, -19.3], ['default spawn', 760, -905], ['Lochergut', 65, -937], ['HB', 1760, -650], ['HB hall', 1740, -640], ...places];
const b = await launch();
const { page } = await open(b, vp, `${BASE}/?at=789,-873,0&t=12:00&nopost`);
let bad = 0;
for (const [name, x, y] of T) {
  const r = await page.evaluate(async ([x, y]) => {
    const t0 = performance.now(); const [fx, fy] = await window.sbxFindSpot(x, y);
    const t = window.sbxTiles; await t.update(fx, fy);
    return { fx, fy, ms: Math.round(performance.now() - t0), inside: t.colliders.inside(fx, fy), play: t.inPlay(fx, fy), water: t.inWater(fx, fy), road: t.onRoad(fx, fy) };
  }, [x, y]);
  const moved = Math.hypot(r.fx - x, r.fy - y);
  const fail = r.inside || !r.play || r.water;
  if (fail) bad++;
  console.log(fail ? 'FAIL' : 'ok  ', name.padEnd(28), 'moved', moved.toFixed(1).padStart(5), 'm', r.ms + 'ms', r.road ? 'road' : '', fail ? JSON.stringify(r) : '');
}
console.log(bad ? `FAIL ${bad}/${T.length}` : `PASS ${T.length} spots`);
await b.close();
process.exit(bad ? 1 : 0);
