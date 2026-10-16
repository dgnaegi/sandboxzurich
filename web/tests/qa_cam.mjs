// QA: camera too close to / inside walls while walking along façades (camera within 0.45 m of a footprint edge or inside it)
import { launch, open, OUT } from './qa_lib.mjs';
const BASE = process.argv[2] ?? 'http://localhost:5199';
const SP = [['Langstrasse', 842, -483], ['Helvetiaplatz', 789, -873], ['Kanzlei', 670, -964], ['Hohlstrasse', 745, -737], ['Lochergut', 65, -937], ['Josefwiese', 514, 197]];
const b = await launch();
const { page, log } = await open(b, 'pc', `${BASE}/?at=842,-483,0&t=12:00&nopost`);
let shots = 0;
for (const [n, x, y] of SP) {
  await page.evaluate(async ([x, y]) => { await window.sbxTiles.update(x, y); window.sbxPlayer.teleport(x, y, 0); }, [x, y]);
  await page.waitForTimeout(1500);
  let bad = 0, tot = 0, worst = null;
  for (let k = 0; k < 8; k++) {
    // start next to a wall: search nearest building footprint point
    await page.evaluate(([x, y, k]) => {
      const t = window.sbxTiles, p = window.sbxPlayer; const a0 = k * Math.PI / 4;
      for (let r = 6; r < 60; r += 1) { const px = x + Math.cos(a0) * r, py = y + Math.sin(a0) * r; if (t.colliders.inside(px, py)) { const [qx, qy] = t.colliders.resolve(px, py, 0.8); p.teleport(qx, qy, a0 + Math.PI / 2); return; } }
      p.teleport(x, y, a0);
    }, [x, y, k]);
    await page.waitForTimeout(300);
    await page.keyboard.down('KeyW');
    for (let i = 0; i < 24; i++) {
      await page.waitForTimeout(150);
      const r = await page.evaluate(() => { const c = window.sbxCamera, t = window.sbxTiles; const cx = c.position.x, cy = -c.position.z; const [qx, qy] = t.colliders.resolve(cx, cy, 0.45); return { ins: t.colliders.inside(cx, cy), d: Math.hypot(qx - cx, qy - cy), cx, cy, h: c.position.y - window.sbxPlayer.z }; });
      tot++; if (r.ins || r.d > 0.02) { bad++; if (!worst || r.ins) worst = r; }
    }
    await page.keyboard.up('KeyW');
    if (worst && shots < 8 && bad > 3) { await page.screenshot({ path: `${OUT}qa_review_cam_${n}_${k}.jpg`, type: 'jpeg', quality: 55 }); shots++; }
  }
  console.log(n, `camera within 0.45 m of wall / inside: ${bad}/${tot} samples`, worst && JSON.stringify({ ins: worst.ins, cx: +worst.cx.toFixed(1), cy: +worst.cy.toFixed(1) }));
}
console.log('errors', log.errors.slice(0, 3));
await b.close();
