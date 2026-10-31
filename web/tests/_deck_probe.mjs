// Probe what the player collides with at a point: static colliders, deck heights, railing push, transit obstacles.
//   node tests/_deck_probe.mjs x y [z] [base-url]
import { chromium } from 'playwright';
const [x, y] = [+process.argv[2], +process.argv[3]], z = process.argv[4] !== undefined ? +process.argv[4] : null, BASE = process.argv[5] ?? 'http://localhost:5190';
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await b.newContext({ viewport: { width: 640, height: 360 } })).newPage();
await page.goto(`${BASE}/?at=${x},${y},0${z !== null ? ',' + z : ''}&t=12:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
await page.waitForTimeout(1500);
const r = await page.evaluate(({ x, y }) => {
  const T = window.sbxTiles, P = window.sbxPlayer, out = { player: [P.x, P.y, P.z] };
  const pz = P.z;
  out.ground = T.ground(x, y); out.deck = T.bridges.heightAt(x, y, pz, 3, 3); out.deck_wide = T.bridges.heightAt(x, y, pz, 12, 12);
  out.rail = T.bridges.railPush(x, y, pz, 0.5);
  const C = T.colliders; out.colliders_inside = C.inside ? C.inside(x, y) : 'n/a';
  out.colliders_resolve = C.resolveCircles ? C.resolveCircles(x, y, 0.9) : 'n/a';
  out.collider_keys = Object.keys(C).slice(0, 12);
  out.near_colliders = (C.list ?? C.items ?? C.polys ?? []).filter?.((p) => Array.isArray(p) && p.some?.((q) => Array.isArray(q) && Math.hypot(q[0] - x, q[1] - y) < 4)).slice(0, 6);
  return out;
}, { x, y });
console.log(JSON.stringify(r));
await b.close();
