// Before/after shots of ramps: fixed viewpoints per site -> preview/ramps/<tag>_<site>_<n>.png and a contact sheet per site.
//   node tests/ramp_shots.mjs <tag> [site-filter] [base-url]
// Viewpoints: x, y (player position), yaw (radians, 0 = north, clockwise), pitch (camera), optional z height hint (deck pick), label.
import { chromium } from 'playwright';
import { execSync } from 'node:child_process';
import fs from 'node:fs';

const tag = process.argv[2] ?? 'now', filt = process.argv[3] ?? '', BASE = process.argv[4] ?? 'http://localhost:5190';
const SITES = {
  gerold: [   // Geroldrampe: Hardbruecke -> Geroldstrasse beside the Freitag tower
    { x: 262, y: 192, yaw: -1.35, pitch: 0.2, label: 'from Geroldstrasse, looking at the ramp foot' },
    { x: 205, y: 215, yaw: 2.6, pitch: 0.15, label: 'beside the Freitag tower, looking up the ramp' },
    { x: 150, y: 185, yaw: -0.3, pitch: 0.2, label: 'under the ramp from the south' },
    { x: 112, y: 241, yaw: 1.9, pitch: 0.4, z: 0.3, label: 'from the Hardbruecke deck at the upper branch, looking over the fork' },
    { x: 105, y: 222, yaw: 1.5, pitch: 0.45, z: 0.6, label: 'from the Hardbruecke deck, looking down the ramp' },
  ],
  duttweiler: [   // Duttweilerbruecke south ramp
    { x: -612, y: 95, yaw: -0.15, pitch: 0.2, label: 'from the south, ramp end' },
    { x: -582, y: 128, yaw: -0.75, pitch: 0.2, label: 'from the south-east' },
    { x: -598, y: 185, yaw: 3.0, pitch: 0.35, z: -2.2, label: 'on the deck, downhill south' },
    { x: -630, y: 140, yaw: 1.3, pitch: 0.2, label: 'from the west, side view' },
  ],
};
const sites = Object.entries(SITES).filter(([k]) => !filt || k.includes(filt));
const outDir = new URL('../../preview/ramps/', import.meta.url).pathname;
fs.mkdirSync(outDir, { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await b.newContext({ viewport: { width: 640, height: 360 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
const first = sites[0][1][0];
await page.goto(`${BASE}/?at=${first.x},${first.y},0&t=14:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
await page.waitForTimeout(1500);
for (const [site, views] of sites) {
  const files = [];
  for (const [i, v] of views.entries()) {
    // one page load per view: ?at=x,y,yaw[,z] places the player (z = height hint picks the deck), then the camera pitch
    await page.goto(`${BASE}/?at=${v.x},${v.y},${v.yaw}${v.z !== undefined ? ',' + v.z : ''}&t=14:00&nopost`);
    await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
    await page.evaluate((v) => { const P = window.sbxPlayer; P.yaw = v.yaw; P.pitch = v.pitch; }, v);
    await page.waitForTimeout(2500);
    const f = `${outDir}${tag}_${site}_${i}.png`;
    await page.screenshot({ path: f });
    files.push(f);
    const z = await page.evaluate(() => +window.sbxPlayer.z.toFixed(2));
    console.log(`${tag} ${site} ${i} ${v.label} (z ${z})`);
  }
  // contact sheet: 2 columns
  execSync(`python3 - <<'PY'
from PIL import Image, ImageDraw
files = ${JSON.stringify(files)}
labels = ${JSON.stringify(views.map((v) => v.label))}
cols = 2; rows = (len(files) + cols - 1) // cols
W = Image.new('RGB', (640 * cols, 380 * rows), (20, 20, 20))
d = ImageDraw.Draw(W)
for i, f in enumerate(files):
    im = Image.open(f)
    x, y = (i % cols) * 640, (i // cols) * 380
    W.paste(im, (x, y + 20))
    d.text((x + 6, y + 4), f"${tag} / ${site} {i}: " + labels[i], fill=(255, 255, 255))
W.save("${outDir}${tag}_${site}_sheet.jpg", quality=88)
PY`);
  console.log(`sheet ${outDir}${tag}_${site}_sheet.jpg`);
}
await b.close();
