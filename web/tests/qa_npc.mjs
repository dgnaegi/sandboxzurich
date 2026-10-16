// QA: NPC / traffic / tram audit at hot spots: peds inside buildings or on rail land, cars inside buildings, car-car overlaps, stuck traffic, T-pose proxy.
import { launch, open, OUT } from './qa_lib.mjs';
import fs from 'fs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const SPOTS = [['Langstrasse', 731, -602], ['Helvetiaplatz', 789, -873], ['Hardbruecke', -13, 150], ['Limmatplatz', 718, 410], ['Albisriederplatz', -495, -641], ['Altstetten', -2095, 704], ['Kalkbreite', 393, -1202], ['Letzigrund', -1003, 13]];
const b = await launch();
const { page, log } = await open(b, 'pc', `${BASE}/?at=731,-602,0&t=12:00&nopost`);
await page.evaluate(async () => { const m = await import('/src/world/railzone.ts'); await m.loadRailZone(); window.__inRail = m.inRail; });
const out = [];
for (const [name, x, y] of SPOTS) {
  await page.evaluate(async ([x, y]) => { await window.sbxTiles.update(x, y); window.sbxPlayer.teleport(x, y, 0); window.__qa = { pedIn: new Map(), pedRail: new Map(), carIn: new Map(), pairs: new Set(), still: new Map(), last: new Map(), n: 0, maxPeds: 0, maxCars: 0, pedPed: new Set() }; }, [x, y]);
  await page.waitForTimeout(1500);
  // sample 30 s
  for (let i = 0; i < 60; i++) {
    await page.waitForTimeout(500);
    await page.evaluate(() => {
      const Q = window.__qa, t = window.sbxTiles, p = window.sbxPlayer, peds = window.sbxCrowd.peds;
      Q.n++;
      let np = 0;
      for (const d of peds) {
        if (!d.h.root.visible && !d.h.root.parent?.visible) continue;
        if (Math.hypot(d.x - p.x, d.y - p.y) > 120) continue;
        np++;
        const id = d.h.id ?? peds.indexOf(d);
        if (t.colliders.inside(d.x, d.y)) Q.pedIn.set(id, [+d.x.toFixed(1), +d.y.toFixed(1)]);
        if (window.__inRail(d.x, d.y)) Q.pedRail.set(id, [+d.x.toFixed(1), +d.y.toFixed(1)]);
        const l = Q.last.get(id);
        if (l && Math.hypot(l[0] - d.x, l[1] - d.y) < 0.05) Q.still.set(id, (Q.still.get(id) ?? 0) + 1); else Q.still.set(id, 0);
        Q.last.set(id, [d.x, d.y]);
      }
      Q.maxPeds = Math.max(Q.maxPeds, np);
      const cars = window.sbxTraffic.positions().filter((v) => Math.hypot(v.x - p.x, v.y - p.y) < 150);
      Q.maxCars = Math.max(Q.maxCars, cars.length);
      for (let i = 0; i < cars.length; i++) {
        const c = cars[i];
        if (c.kind === 'car' && t.colliders.inside(c.x, c.y)) Q.carIn.set(i + ':' + (c.id ?? ''), [+c.x.toFixed(1), +c.y.toFixed(1)]);
        for (let j = i + 1; j < cars.length; j++) if (cars[j].kind === 'car' && c.kind === 'car' && Math.hypot(c.x - cars[j].x, c.y - cars[j].y) < 2.0) Q.pairs.add(`${c.x.toFixed(0)},${c.y.toFixed(0)}`);
      }
    });
  }
  const r = await page.evaluate(() => { const Q = window.__qa; return { peds: Q.maxPeds, cars: Q.maxCars, pedInBuilding: [...Q.pedIn.values()].slice(0, 6), pedInBuildingN: Q.pedIn.size, pedOnRail: [...Q.pedRail.values()].slice(0, 6), pedOnRailN: Q.pedRail.size, carInBuilding: [...Q.carIn.values()].slice(0, 6), carInN: Q.carIn.size, carOverlap: [...Q.pairs].slice(0, 6), pedStuck60s: [...Q.still.values()].filter((v) => v > 40).length }; });
  await page.screenshot({ path: `${OUT}qa_review_npc_${name}.jpg`, type: 'jpeg', quality: 55 });
  console.log(name, JSON.stringify(r));
  out.push({ name, ...r });
}
console.log('errors', log.errors.slice(0, 5), 'bad', log.bad.slice(0, 5));
await b.close();
