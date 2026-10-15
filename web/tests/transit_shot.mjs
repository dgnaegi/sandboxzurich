// Plausibility check for web/public/data/transit.json (no browser needed).
import { readFileSync } from 'node:fs';
const { lines } = JSON.parse(readFileSync(new URL('../public/data/transit.json', import.meta.url)));
let bad = 0;
const fail = (m) => { bad++; console.log('FAIL', m); };
if (!lines.length) fail('no lines');
for (const l of lines) {
  let len = 0, maxJump = 0;
  for (let i = 1; i < l.pts.length; i++) { const d = Math.hypot(l.pts[i][0] - l.pts[i - 1][0], l.pts[i][1] - l.pts[i - 1][1]); len += d; maxJump = Math.max(maxJump, d); }
  const inArea = l.pts.some(([x, y]) => x >= 600 && x <= 1200 && y >= -1000 && y <= -400);
  const sorted = l.stops.every((s, i) => i === 0 || s.s > l.stops[i - 1].s);
  const ok = len > 150 && maxJump < 150 && inArea && sorted && l.stops.length > 0 && l.stops.every((s) => s.s >= 0 && s.s <= len + 1);
  console.log(ok ? 'ok  ' : 'FAIL', l.ref.padEnd(4), l.mode.padEnd(10), 'dir', l.dir, `${len.toFixed(0)}m`, `maxseg ${maxJump.toFixed(0)}m`, l.stops.map((s) => `${s.name}@${s.s.toFixed(0)}`).join(', '));
  if (!ok) bad++;
}
process.exit(bad ? 1 : 0);
