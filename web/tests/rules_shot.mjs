// Oblique/top shots: node tests/rules_shot.mjs out.png x y size [elev_deg=90] [az_deg=0] [px=800] [hour=12:00]
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const [,, out, x, y, size = '60', elev = '90', az = '0', px = '800', t = '12:00'] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: Number(px), height: Number(px) } })).newPage();
await p.goto(`http://localhost:5173/?at=${x},${y},0&t=${t}`);
await p.waitForFunction(() => window.sbxReady && window.sbxPlayer, null, { timeout: 60000 });
await p.waitForTimeout(9000);
const url = await p.evaluate(([x, y, size, elev, az]) => {
  const { sbxRenderer: r, sbxScene: s, sbxCamera: c0, sbxTiles: t, sbxPlayer: pl } = window;
  pl.mesh.visible = false;
  t.cull(x, y, 400);
  const c = c0.clone(), D = elev > 60 ? 400 : size * 3, e = elev * Math.PI / 180, a = az * Math.PI / 180;
  c.fov = 2 * Math.atan(size / 2 / D) * 180 / Math.PI; c.aspect = 1; c.near = 0.5; c.far = D + 600;
  const gy = (window.sbxGround ? window.sbxGround(x, y) : 0);
  c.position.set(x + Math.sin(a) * Math.cos(e) * D, gy + Math.sin(e) * D, -y - Math.cos(a) * Math.cos(e) * D);
  c.up.set(0, 1, 0); if (elev > 85) c.up.set(0, 0, -1);
  c.lookAt(x, gy, -y); c.updateProjectionMatrix();
  const fog = s.fog; s.fog = null;
  r.setSize(r.domElement.width, r.domElement.width, false);
  r.render(s, c); const d = r.domElement.toDataURL('image/png'); s.fog = fog; return d;
}, [Number(x), Number(y), Number(size), Number(elev), Number(az)]);
writeFileSync(out, Buffer.from(url.split(',')[1], 'base64'));
await b.close();
