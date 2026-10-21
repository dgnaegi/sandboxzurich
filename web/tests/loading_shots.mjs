// Reproducible loading-screen source stills: free-camera shots -> research/loading_stills/*.jpg (1280x720) + manifest.json
// (not served; pipeline/loading_video.py turns them into the intro video in web/public/loading/)
// usage: node tests/loading_shots.mjs [file-prefix-filter]   (dev server on :5173 must run)
import { chromium } from 'playwright';
import sharp from 'sharp';
import fs from 'node:fs';
const OUT = new URL('../../research/loading_stills/', import.meta.url).pathname;
fs.mkdirSync(OUT, { recursive: true });
// fx/fy: focus point (0..1) used for the centred cover crop on portrait screens
const SHOTS = [
  { file: 'hardbruecke', caption: 'HARDBRÜCKE · KREIS 5', fx: 0.55, fy: 0.5, at: '-20,-90,0', t: '19:05', cam: [-20, -90, 28], look: [45, 223, 70], fov: 50 },
  { file: 'langstrasse', caption: 'LANGSTRASSE · KREIS 4', fx: 0.55, fy: 0.5, at: '690,-800,0', t: '22:30', cam: [690, -850, 22], look: [800, -520, 6], fov: 50 },
  { file: 'letzigrund', caption: 'LETZIGRUND · KREIS 9', fx: 0.5, fy: 0.5, at: '-900,-300,0', t: '19:30', cam: [-900, -330, 70], look: [-969, -166, 5], fov: 55 },
  { file: 'lochergut', caption: 'LOCHERGUT · KREIS 4', fx: 0.72, fy: 0.5, at: '60,-1000,0', t: '18:20', cam: [-40, -1080, 45], look: [105, -890, 35], fov: 50 },
  { file: 'schlachthof', caption: 'SCHLACHTHOF · KREIS 9', fx: 0.25, fy: 0.5, at: '-760,-40,0', t: '17:45', cam: [-760, -40, 25], look: [-850, 30, 8], fov: 55 },
  { file: 'limmatplatz', caption: 'LIMMATPLATZ · KREIS 5', fx: 0.45, fy: 0.5, at: '1180,-40,0', t: '17:30', cam: [1130, 70, 35], look: [1240, 10, 6], fov: 50 },
  { file: 'bullingerplatz', caption: 'BULLINGERPLATZ · KREIS 4', fx: 0.45, fy: 0.55, at: '-60,-470,0', t: '12:30', cam: [-70, -470, 4], look: [-37, -497, 3], fov: 60 },
  { file: 'johanneskirche', caption: 'JOHANNESKIRCHE · KREIS 5', fx: 0.82, fy: 0.5, at: '1180,-40,0', t: '20:30', cam: [1250, -120, 30], look: [1230, 20, 8], fov: 50 },
  { file: 'hauptbahnhof', caption: 'HAUPTBAHNHOF · KREIS 1', fx: 0.6, fy: 0.55, at: '1600,-480,0', t: '18:10', cam: [1600, -480, 50], look: [1760, -650, 15], fov: 55 },
];
const only = process.argv[2];
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const page = await (await b.newContext({ viewport: { width: 1600, height: 900 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
for (const s of SHOTS) {
  if (only && !s.file.startsWith(only)) continue;
  await page.goto(`http://localhost:5173/?at=${s.at}&t=${s.t}`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.addStyleTag({ content: 'body > *:not(canvas){visibility:hidden !important}' });
  await page.evaluate((s) => {
    for (const c of document.querySelectorAll('canvas')) if (c !== window.sbxRenderer.domElement) c.style.display = 'none';
    const r = window.sbxRenderer, orig = r.render.bind(r), cam = window.sbxCamera, P = window.sbxPlayer, T = window.sbxTiles;
    r.render = (sc, c) => {
      if (c === cam) {
        const [x, y, h] = s.cam, [lx, ly, lh] = s.look;
        cam.fov = s.fov; cam.updateProjectionMatrix();
        cam.position.set(x, T.ground(x, y) + h, -y); cam.lookAt(lx, T.ground(lx, ly) + lh, -ly);
        P.mesh.visible = false;
      }
      orig(sc, c);
    };
  }, s);
  await page.waitForTimeout(9000);
  const png = await page.screenshot({ type: 'png' });
  let q = 74, buf;
  do { buf = await sharp(png).resize(1280, 720).jpeg({ quality: q, mozjpeg: true }).toBuffer(); q -= 4; } while (buf.length > 120000 && q > 40);
  fs.writeFileSync(`${OUT}${s.file}.jpg`, buf);
  console.log(s.file, buf.length, 'q', q + 4);
}
await b.close();
fs.writeFileSync(`${OUT}manifest.json`, JSON.stringify(SHOTS.map(({ file, caption, fx, fy }) => ({ file: `${file}.jpg`, caption, fx, fy })), null, 1) + '\n');
