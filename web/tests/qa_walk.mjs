// QA: run in 8 directions from many places; detect stalls, wall clipping, z jumps, camera inside buildings.
import { launch, open, OUT } from './qa_lib.mjs';
import fs from 'fs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const places = JSON.parse(fs.readFileSync(new URL('../public/map/map.json', import.meta.url))).places.filter((p) => p.built);
const b = await launch();
const { page, log } = await open(b, 'pc', `${BASE}/?at=${places[0].x},${places[0].y},0&t=12:00&nopost`, { wait: false });
await page.addInitScript(() => {
  const S = (window.__qa = { s: [] });
  setInterval(() => { if (!window.sbxPlayer) return;
    const p = window.sbxPlayer, c = window.sbxCamera, t = window.sbxTiles;
    S.s.push({ t: performance.now(), x: p.x, y: p.y, z: p.z, v: p.speed, ins: t.colliders.inside(p.x, p.y), cins: t.colliders.inside(c.position.x, -c.position.z), cz: c.position.y, inPlay: t.inPlay(p.x, p.y) });
  }, 50);
});
await page.reload(); await page.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
let reloads = 0;
page.on('framenavigated', (f) => { if (f === page.mainFrame()) reloads++; });
const results = [];
for (const pl of places) {
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
  await page.evaluate(async (pl) => { await window.sbxTiles.update(pl.x, pl.y); window.sbxPlayer.teleport(pl.x, pl.y, 0); }, pl);
  await page.waitForTimeout(1200);
  for (let k = 0; k < 8; k++) {
    const yaw = (k * Math.PI) / 4;
    // find free start
    const st = await page.evaluate(({ pl, yaw }) => {
      const p = window.sbxPlayer, t = window.sbxTiles;
      for (let r = 0, a = 0; r < 40; r += 0.5, a += 0.9) { const px = pl.x + Math.cos(a) * r, py = pl.y + Math.sin(a) * r; if (!t.colliders.inside(px, py)) { p.teleport(px, py, yaw); break; } }
      window.__qa.s.length = 0; return [p.x, p.y];
    }, { pl, yaw });
    await page.waitForTimeout(400); await page.evaluate(() => (window.__qa.s.length = 0));
    await page.keyboard.down('Shift'); await page.keyboard.down('KeyW');
    await page.waitForTimeout(5000);
    await page.keyboard.up('KeyW'); await page.keyboard.up('Shift');
    const r = await page.evaluate(() => {
      const s = window.__qa.s; if (s.length < 20) return { n: s.length, lost: true }; let stall = 0, maxdz = 0, ins = 0, cins = 0, out = 0, maxdz_i = 0;
      for (let i = 1; i < s.length; i++) {
        if (i > 20 && s[i].v < 0.6) stall += 0.05;
        const dz = Math.abs(s[i].z - s[i - 1].z); if (dz > maxdz) { maxdz = dz; maxdz_i = i; }
        if (s[i].ins) ins++; if (s[i].cins) cins++; if (!s[i].inPlay) out++;
      }
      const e = s[s.length - 1] ?? s[0];
      return { n: s.length, stall: +stall.toFixed(1), maxdz: +maxdz.toFixed(2), ins, cins, out, end: [+e.x.toFixed(1), +e.y.toFixed(1)], dist: Math.hypot(e.x - s[0].x, e.y - s[0].y) | 0, at: s[maxdz_i] && [+s[maxdz_i].x.toFixed(1), +s[maxdz_i].y.toFixed(1)] };
    });
    if (r.lost) console.log('lost samples (page reload?)', pl.name, yaw, 'navs', reloads);
    results.push({ place: pl.name, yaw: +yaw.toFixed(2), start: st.map((v) => +v.toFixed(1)), ...r });
  }
}
fs.writeFileSync('/private/tmp/claude-501/-Users-danielgnagi-sandboxzurich/c6777b7a-a5e5-418a-994d-c9027f86d233/scratchpad/qa_walk.json', JSON.stringify(results, null, 1));
console.log('errors', log.errors, 'bad', log.bad);
for (const r of results) if (r.stall > 1.5 || r.maxdz > 0.35 || r.ins || r.cins > 2 || r.out) console.log(JSON.stringify(r));
console.log('total runs', results.length, 'navigations', reloads);
await b.close();
