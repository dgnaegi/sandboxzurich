// node measure_attach.mjs  -> measures rig bones in three.js and writes accessories/manifest.json + preview/humans_acc_sheet.jpg
import { chromium } from "/Users/danielgnagi/gtazurich/web/node_modules/playwright/index.mjs";
import { spawn } from "node:child_process"; import fs from "node:fs";
const R = "/Users/danielgnagi/gtazurich";
const br = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"] }); const pg = await br.newPage();
pg.on("console", (m) => { if (m.type() === "error") console.log("ERR", m.text()); }); pg.on("pageerror", (e) => console.log("PAGEERR", e.message));
const MIME = { html: "text/html", js: "text/javascript", mjs: "text/javascript", glb: "model/gltf-binary", json: "application/json" };
await pg.route("http://acc.test/**", (rt) => { const f = R + new URL(rt.request().url()).pathname; if (!fs.existsSync(f)) return rt.fulfill({ status: 404, body: "" });
  rt.fulfill({ body: fs.readFileSync(f), contentType: MIME[f.split(".").pop()] || "application/octet-stream" }); });
await pg.goto("http://acc.test/pipeline/blender/check/viewer.html"); await pg.waitForFunction("window.ready");
const BONES = ["spine_03", "pelvis", "hand_r", "hand_l", "middle_01_r", "middle_01_l", "upperarm_r", "upperarm_l", "head"];
const REF = "npc_01";   // adult male reference rig (all NPCs share bone names/hierarchy)
const M = await pg.evaluate(([i, b]) => window.measure(i, "idle", b), [REF, BONES]);
const MP = await pg.evaluate(([i, b]) => window.measure(i, "stand_phone", b), [REF, BONES]);
const fs3 = JSON.parse(fs.readFileSync(R + "/pipeline/blender/accessories_place.json", "utf8"));
// quaternion helpers
const qinv = (q) => [-q[0], -q[1], -q[2], q[3]];
const qmul = (a, b) => [a[3]*b[0]+a[0]*b[3]+a[1]*b[2]-a[2]*b[1], a[3]*b[1]-a[0]*b[2]+a[1]*b[3]+a[2]*b[0], a[3]*b[2]+a[0]*b[1]-a[1]*b[0]+a[2]*b[3], a[3]*b[3]-a[0]*b[0]-a[1]*b[1]-a[2]*b[2]];
const qrot = (q, v) => { const u = [q[0], q[1], q[2]], w = q[3]; const c = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]; const t = c(u, v).map((x) => 2 * x); const t2 = c(u, t); return v.map((x, k) => x + w * t[k] + t2[k]); };
const eul = (q) => { const [x, y, z, w] = q; const m02 = 2*(x*z+w*y), m00 = 1-2*(y*y+z*z), m01 = 2*(x*y-w*z), m12 = 2*(y*z-w*x), m22 = 1-2*(x*x+y*y), m11 = 1-2*(x*x+z*z), m10 = 2*(x*y+w*z);
  const ey = Math.asin(Math.max(-1, Math.min(1, m02))); let ex, ez; if (Math.abs(m02) < 0.9999) { ex = Math.atan2(-m12, m22); ez = Math.atan2(-m01, m00); } else { ex = Math.atan2(m21 ?? 2*(y*z+w*x), m11); ez = 0; } return [ex, ey, ez]; };
const eq = (e) => { const [a, b, c] = e.map((v) => v / 2); const [cx, cy, cz, sx, sy, sz] = [Math.cos(a), Math.cos(b), Math.cos(c), Math.sin(a), Math.sin(b), Math.sin(c)];
  return [sx*cy*cz + cx*sy*sz, cx*sy*cz - sx*cy*sz, cx*cy*sz + sx*sy*cz, cx*cy*cz - sx*sy*sz]; };
const mid = (a, b) => a.map((v, i) => (v + b[i]) / 2);
const out = [];
for (const [name, s] of Object.entries(fs3)) {
  const meas = s.pose === "phone" ? MP : M; let e = { name, file: s.file || name + ".glb" };
  if (s.bone) {
    const bn = meas[s.bone]; let anchor = bn.p;
    if (s.anchor === "palm_r") anchor = mid(meas.hand_r.p, meas.middle_01_r.p); if (s.anchor === "palm_l") anchor = mid(meas.hand_l.p, meas.middle_01_l.p);
    const world = s.delta.map((d, i) => anchor[i] + d - bn.p[i]); const qi = qinv(bn.q);
    e.bone = s.bone; e.offset = qrot(qi, world).map((v) => +v.toFixed(4));
    e.rotation = eul(qmul(qi, eq(s.rot || [0, 0, 0]))).map((v) => +v.toFixed(4));
  } else {   // root-relative (character space): anchor = hands midpoint
    const hm = mid(meas.hand_r.p, meas.hand_l.p); e.bone = null;
    e.offset = (s.anchor === "hands" ? [hm[0] + s.delta[0], hm[1] + s.delta[1], hm[2] + s.delta[2]] : s.delta).map((v) => +v.toFixed(4)); e.rotation = s.rot || [0, 0, 0];
  }
  for (const k of ["scale", "tint", "pose", "note", "anim", "attach_to"]) if (s[k] !== undefined) e[k] = s[k];
  out.push(e);
}
fs.writeFileSync(R + "/web/public/models/accessories/manifest.json", JSON.stringify({ units: "metres, bone-local (three.js Object3D under the bone) or character-root-local when bone=null", reference_rig: REF, items: out }, null, 1));
// preview sheet
const info = JSON.parse(fs.readFileSync(R + "/pipeline/blender/accessories_scenes.json", "utf8"));
const shots = [];
for (const sc of info) {
  const items = sc.items.map((it) => ({ ...it, acc: (it.acc || []).map((n) => { const a = typeof n === "string" ? { n } : n; const m = out.find((o) => o.name === a.n); return { file: m.file, bone: m.bone, offset: m.offset, rotation: m.rotation, scale: a.scale ?? m.scale, color: a.color ?? m.tint, at: a.at }; }) }));
  await pg.setViewportSize({ width: sc.w, height: sc.h });
  await pg.evaluate(([i, c]) => { document.querySelectorAll("canvas").forEach((x) => x.remove()); return window.show(i, c); }, [items, { w: sc.w, h: sc.h, pos: sc.pos, look: sc.look, fov: sc.fov }]);
  const f = `/private/tmp/claude-501/-Users-danielgnagi-gtazurich/2c85f10e-b4e1-4c95-8bd3-e132013d6298/scratchpad/acc_${shots.length}.png`; await pg.screenshot({ path: f }); shots.push(f);
}
fs.writeFileSync("/private/tmp/claude-501/-Users-danielgnagi-gtazurich/2c85f10e-b4e1-4c95-8bd3-e132013d6298/scratchpad/acc_shots.json", JSON.stringify(shots));
await br.close();
