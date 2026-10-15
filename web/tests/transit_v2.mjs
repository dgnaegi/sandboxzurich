// Transit contact sheet (tram front 3/4, tram night, bus, stop) -> ../preview/transit_v2.jpg via sheet at end
import { chromium } from 'playwright';
import { execSync } from 'node:child_process';
const OUT = new URL('../../preview/', import.meta.url).pathname;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const pg = await (await b.newContext({ viewport: { width: 900, height: 520 } })).newPage();
pg.on('pageerror', (e) => console.log('pageerror', e.message));
const jobs = [['tram', '11:00', 'tram', 0], ['tramn', '22:30', 'tram', 0], ['bus', '11:00', 'bus', 0], ['stop', '15:00', 'stop', 0]];
for (const [name, t, kind] of jobs.filter((j) => !process.argv[2] || process.argv[2].split(',').includes(j[0]))) {
  await pg.goto(`http://localhost:5173/?at=785,-635,0&t=${t}`);
  await pg.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
  const res = await pg.evaluate(async ([kind, name]) => {
    const tr = window.sbxTransit, P = window.sbxPlayer, cam = window.sbxCamera, rd = window.sbxRenderer;
    let target = null; // {fx, fy, hx, hy, look height}
    if (kind === 'stop') {
      let best = null;
      for (const l of tr.lines) if (l.tram) for (const g of l.segs) { const q = [0, 0]; tr.sample(l, g.s1 - 18.5, q); const d = Math.hypot(q[0] - 785, q[1] + 635); if (!best || d < best.d) best = { d, l, g }; }
      const { l, g } = best, o = [0, 0], o2 = [0, 0];
      tr.sample(l, g.s1 - 20.5, o); tr.sample(l, g.s1 - 16.5, o2);
      const h = Math.atan2(o2[0] - o[0], o2[1] - o[1]);
      target = { x: o[0] + Math.cos(h) * 2.6, y: o[1] - Math.sin(h) * 2.6, hx: Math.sin(h), hy: Math.cos(h), stop: true };
      P.x = target.x; P.y = target.y;
    } else {
      const want = kind === 'bus' ? [9.2, 8.4] : [6.9, 7.8];
      const spots = tr.lines.filter((l) => (kind === 'bus') === !l.tram).flatMap((l) => l.segs.map((g) => { const o = [0, 0]; tr.sample(l, g.s1 - 20, o); return o; })).sort((a, b) => Math.hypot(a[0] - 785, a[1] + 635) - Math.hypot(b[0] - 785, b[1] + 635));
      outer: for (let i = 0; i < spots.length; i += 2) {
        P.x = spots[i][0]; P.y = spots[i][1];
        for (let k = 0; k < 8; k++) {
          await new Promise((r) => setTimeout(r, 150));
          const cs = tr.colliders();
          for (let j = 0; j + 1 < cs.length; j++) {
            const c = cs[j], n = cs[j + 1];
            if (Math.hypot(c.x - P.x, c.y - P.y) < 60 && Math.abs(c.len - want[0]) < .05 && Math.hypot(n.x - c.x, n.y - c.y) < 9 && Math.abs(n.len - c.len) > .05 && (kind === 'bus' || c.len > 6.8)) {
              const hx = Math.cos(c.heading), hy = Math.sin(c.heading);
              target = { x: c.x + hx * c.len / 2, y: c.y + hy * c.len / 2, hx, hy }; break outer;
            }
          }
        }
      }
    }
    if (!target) return null;
    const { x, y, hx, hy } = target;
    const rx = hy, ry = -hx; // right of travel
    const cx = target.stop ? x - hx * 5 + rx * 4.5 : x + hx * 6.5 + rx * 3.8, cy = target.stop ? y - hy * 5 + ry * 4.5 : y + hy * 6.5 + ry * 3.8;
    P.x = cx; P.y = cy;
    const look = target.stop ? [x + hx * 1, 1.6, y + hy * 1] : [x - hx * 1.5, 1.9, y - hy * 1.5];
    const orig = rd.render.bind(rd);
    rd.render = (s, c) => { cam.position.set(cx, target.stop ? 2.2 : 1.9, -cy); cam.up.set(0, 1, 0); cam.lookAt(look[0], look[1], -look[2]); cam.updateMatrixWorld(true); orig(s, c); };
    return [x, y];
  }, [kind, name]);
  console.log(name, res);
  await pg.waitForTimeout(5000);
  await pg.screenshot({ path: `${OUT}_tv2_${name}.png` });
}
await b.close();
execSync(`${new URL('../../.venv/bin/python', import.meta.url).pathname} -c "
from PIL import Image
ims=[Image.open('${OUT}_tv2_'+n+'.png').resize((800,462)) for n in ['tram','tramn','bus','stop']]
s=Image.new('RGB',(1600,924))
for i,im in enumerate(ims): s.paste(im,((i%2)*800,(i//2)*462))
s.save('${OUT}transit_v2.jpg',quality=82)"`);
