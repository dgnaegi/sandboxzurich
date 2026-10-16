// Traffic legality audit: NPC cars (simulated 2 min of game time at 10 places), bus lines and parked cars are checked
// against the legal-area raster (pipeline/traffic_zones.py -> tests/fixtures/traffic_zones.png: 1 road, 7 deck legal;
// 2 square, 3 pedestrian zone, 4 park, 5 building, 6 rail land, 0 other). FAIL if > 0.5 % of car positions are illegal.
// Usage: node tests/traffic_legal.mjs [baseUrl] [--minutes=2] [--sheet]
import { chromium } from 'playwright';
import sharp from 'sharp';
import fs from 'node:fs';

const BASE = process.argv.find((a) => a.startsWith('http')) ?? 'http://localhost:5173';
const MIN = +(process.argv.find((a) => a.startsWith('--minutes='))?.slice(10) ?? 2);
const LIMIT = 0.5; // percent
const FX = new URL('./fixtures/', import.meta.url).pathname, PREV = new URL('../../preview/', import.meta.url).pathname;
const meta = JSON.parse(fs.readFileSync(FX + 'traffic_zones.json'));
const { data: grid } = await sharp(FX + 'traffic_zones.png').extractChannel(0).raw().toBuffer({ resolveWithObject: true });
const cat = (x, y) => { const i = Math.floor((x - meta.x0) / meta.cell), j = Math.floor((meta.y1 - y) / meta.cell); return i < 0 || j < 0 || i >= meta.w || j >= meta.h ? 0 : grid[j * meta.w + i]; };
const LEGAL = (c) => c === 1 || c === 7;
const NAMES = ['kerb/other', 'road', 'square', 'pedestrian zone', 'park', 'building', 'rail land', 'deck'];
// legal if the centre or any point 0.7 m around it is on a carriageway (raster is 1 m, polygons are exact)
const legalAt = (x, y) => { const c = cat(x, y); if (LEGAL(c)) return [true, c]; for (const [dx, dy] of [[.7, 0], [-.7, 0], [0, .7], [0, -.7]]) if (LEGAL(cat(x + dx, y + dy)) && cat(x + dx, y + dy) !== 2) return [true, c]; return [false, c]; };
// parked car: not on square / pedestrian zone / park / building / rail land, and a carriageway cell within 5 m (kerbside bays are wider than the OSM width)
const parkedOk = (x, y) => { const c = cat(x, y); if (c >= 2 && c <= 6) return [false, c]; if (LEGAL(c)) return [true, c]; for (let r = 1; r <= 5; r++) for (let a = 0; a < 16; a++) if (LEGAL(cat(x + r * Math.cos(a * Math.PI / 8), y + r * Math.sin(a * Math.PI / 8)))) return [true, c]; return [false, c]; };
const PLACES = [
  ['Langstrasse', 753, -557], ['Langstrasse Unterfuehrung', 932, -278], ['Helvetiaplatz', 704, -869], ['Baeckeranlage', 528, -693],
  ['Josefwiese', 437, 439], ['Europaallee/Lagerstrasse', 1290, -594], ['Hardbruecke Deck', 26, 111], ['Escher-Wyss-Platz', -96, 788],
  ['Idaplatz', 237, -1465], ['Lindenplatz', -2470, 400], ['Albisriederplatz', -493, -619],
];

const roads = JSON.parse(fs.readFileSync(new URL('../public/data/roads.json', import.meta.url)));
const eIdx = []; // game edge index -> raw roads.json car edge (buildGraph drops tiny edges)
roads.cars.forEach((r, i) => { const n = r.p.length / 2; if (n < 2) return; let L = 0; for (let k = 1; k < n; k++) L += Math.hypot(r.p[2 * k] - r.p[2 * k - 2], r.p[2 * k + 1] - r.p[2 * k - 1]); if (L >= 1) eIdx.push(i); });

const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await browser.newContext({ viewport: { width: 800, height: 450 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
await page.goto(`${BASE}/?at=${PLACES[0][1]},${PLACES[0][2]},0&t=12:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
await page.waitForTimeout(1500);

const soft = []; // centre cell off the carriageway without tolerance (kerb-side wobble), only shown on the sheet when nothing is illegal
const bad = []; // {place, x, y, edge, cat, kind}
let total = 0, illegal = 0, strict = 0, overhang = 0;
const per = [];
for (const [name, px, py] of PLACES) {
  const samples = await page.evaluate(async ([px, py, min]) => {
    const t = window.sbxTraffic, p = window.sbxPlayer;
    p.teleport(px, py, 0);
    t.maxCars = 60;
    const out = [];
    const steps = Math.round(min * 60 / 0.05);
    for (let i = 0; i < steps; i++) {
      t.update(0.05, px, py, []);
      if (i % 10 === 0) for (const v of t.positions()) if (v.kind === 'car') out.push([v.x, v.y, v.edge, v.id, v.heading, v.len]);
    }
    return out;
  }, [px, py, MIN]);
  let n = 0, ill = 0;
  const seen = new Set();
  for (const [x, y, e, id, hd, ln] of samples) {
    n++;
    if (!LEGAL(cat(x, y))) { strict++; soft.push({ place: name, x, y, edge: eIdx[e], cat: cat(x, y), id }); }
    { const c = Math.cos(hd), s = Math.sin(hd); let o = false; for (const [a, b] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) { const u = a * ln / 2, w = b * 0.9; const cc = cat(x + u * c - w * s, y + u * s + w * c); if (cc >= 2 && cc <= 6) o = true; } if (o) overhang++; }
    const [ok, c] = legalAt(x, y);
    if (!ok) { ill++; bad.push({ place: name, x, y, edge: eIdx[e], cat: c, id }); }
  }
  total += n; illegal += ill;
  per.push({ name, n, ill });
  console.log(`${name.padEnd(28)} ${String(n).padStart(6)} positions, ${String(ill).padStart(4)} illegal (${(100 * ill / Math.max(n, 1)).toFixed(2)} %)`);
}
const pct = 100 * illegal / Math.max(total, 1);

// parked cars: slots in the loaded tiles around each place
let pk = 0, pkBad = 0;
const pkList = [];
for (const [name, px, py] of PLACES) {
  await page.evaluate(([x, y]) => window.sbxPlayer.teleport(x, y, 0), [px, py]);
  await page.waitForTimeout(2500);
  const slots = await page.evaluate(([x, y]) => window.sbxParked.near(x, y, 150).map((s) => [s.x, s.y]), [px, py]);
  for (const [x, y] of slots) { pk++; const [ok, c] = parkedOk(x, y); if (!ok) { pkBad++; pkList.push({ place: name, x: +x.toFixed(1), y: +y.toFixed(1), cat: NAMES[c] }); } }
}
// buses: sample the line polylines (pure function of time on pts), count stretches outside the legal area
const tr = JSON.parse(fs.readFileSync(new URL('../public/data/transit.json', import.meta.url)));
let bs = 0, bsBad = 0;
const busList = [];
for (const L of tr.lines) {
  if (L.mode === 'tram') continue;
  for (let i = 0; i + 1 < L.pts.length; i++) {
    const [x0, y0] = L.pts[i], [x1, y1] = L.pts[i + 1], d = Math.hypot(x1 - x0, y1 - y0), k = Math.max(1, Math.round(d / 2));
    for (let j = 0; j < k; j++) {
      const x = x0 + (x1 - x0) * j / k, y = y0 + (y1 - y0) * j / k;
      if (x < -2550 || x > 1875 || y < -1770 || y > 1155) continue; // play area (config.AREA) minus 40 m; outside no street ground is drawn
      bs++; const [ok, c] = legalAt(x, y);
      if (!ok) { bsBad++; busList.push({ ref: L.ref, x: +x.toFixed(0), y: +y.toFixed(0), cat: NAMES[c] }); }
    }
  }
}

// worst spots: cluster illegal car positions by 12 m cell
const cl = new Map();
const pool = bad.length ? bad : soft;
for (const b of pool) { const k = `${Math.round(b.x / 12)},${Math.round(b.y / 12)}`; const c = cl.get(k) ?? { n: 0, x: 0, y: 0, edges: new Set(), cats: {}, place: b.place }; c.n++; c.x += b.x; c.y += b.y; c.edges.add(b.edge); c.cats[NAMES[b.cat]] = (c.cats[NAMES[b.cat]] ?? 0) + 1; cl.set(k, c); }
const worst = [...cl.values()].sort((a, b) => b.n - a.n).slice(0, 12).map((c) => ({ n: c.n, x: Math.round(c.x / c.n), y: Math.round(c.y / c.n), edges: [...c.edges].slice(0, 4), cats: c.cats, place: c.place }));
console.log('\nworst spots (n, x, y, raw car edges, area):');
for (const w of worst) console.log(`  ${String(w.n).padStart(4)}  ${w.x},${w.y}  edges ${w.edges.join('/')}  ${JSON.stringify(w.cats)}  [${w.place}]`);
console.log(`\nparked cars in loaded tiles: ${pk}, outside carriageway/deck: ${pkBad} (${(100 * pkBad / Math.max(pk, 1)).toFixed(1)} %)`);
console.log(pkList.slice(0, 8).map((p) => `  ${p.x},${p.y} ${p.cat} [${p.place}]`).join('\n'));
console.log(`bus lines: ${bs} samples, ${bsBad} outside the legal area (${(100 * bsBad / Math.max(bs, 1)).toFixed(2)} %)`);
const byRef = {}; for (const b of busList) byRef[b.ref] = (byRef[b.ref] ?? 0) + 1;
console.log('  per line:', JSON.stringify(byRef));
fs.writeFileSync(new URL('../../logs/traffic_legal.json', import.meta.url), JSON.stringify({ total, illegal, pct, strict, overhang, per, worst, pk, pkBad, pkList, bs, bsBad, busList: busList.slice(0, 200) }));

// contact sheet of the worst spots: 160 m crops of the raster, red dots = illegal samples
if (process.argv.includes('--sheet') && worst.length) {
  const S = 160, Z = 3, cols = 4, rows = Math.ceil(Math.min(worst.length, 8) / cols);
  const PAL = [[40, 40, 40], [110, 110, 115], [200, 170, 110], [230, 140, 190], [70, 140, 70], [90, 80, 80], [150, 120, 70], [90, 130, 200]];
  const W = cols * S * Z, H = rows * S * Z, img = Buffer.alloc(W * H * 3);
  worst.slice(0, 8).forEach((w, k) => {
    const ox = (k % cols) * S * Z, oy = Math.floor(k / cols) * S * Z;
    for (let j = 0; j < S * Z; j++) for (let i = 0; i < S * Z; i++) {
      const c = PAL[cat(w.x - S / 2 + i / Z, w.y + S / 2 - j / Z)], o = ((oy + j) * W + ox + i) * 3; img[o] = c[0]; img[o + 1] = c[1]; img[o + 2] = c[2];
    }
    for (const b of pool) {
      const i = Math.round((b.x - (w.x - S / 2)) * Z), j = Math.round((w.y + S / 2 - b.y) * Z);
      for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) { const a = i + dx, d = j + dy; if (a < 0 || d < 0 || a >= S * Z || d >= S * Z) continue; const o = ((oy + d) * W + ox + a) * 3; img[o] = 255; img[o + 1] = 30; img[o + 2] = 30; }
    }
  });
  await sharp(img, { raw: { width: W, height: H, channels: 3 } }).jpeg({ quality: 82 }).toFile(PREV + 'traffic_legal.jpg');
  console.log('sheet', PREV + 'traffic_legal.jpg', 'spots:', worst.slice(0, 8).map((w) => `${w.x},${w.y}`).join(' | '));
}
console.log(`info: centre on carriageway cell (no tolerance) misses ${strict} (${(100 * strict / total).toFixed(2)} %); body corners on squares/pedestrian zones/parks/buildings/rail ${overhang} (${(100 * overhang / total).toFixed(2)} %)`);
console.log(`\n${pct <= LIMIT ? 'OK  ' : 'FAIL'} cars: ${illegal}/${total} illegal positions = ${pct.toFixed(2)} % (limit ${LIMIT} %)`);
if (pct > LIMIT) process.exitCode = 1;
const pkPct = 100 * pkBad / Math.max(pk, 1);
console.log(`${pkPct <= LIMIT ? 'OK  ' : 'FAIL'} parked cars: ${pkBad}/${pk} off the carriageway = ${pkPct.toFixed(2)} % (limit ${LIMIT} %)`);
if (pkPct > LIMIT) process.exitCode = 1;
await browser.close();
