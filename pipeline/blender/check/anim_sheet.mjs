// node anim_sheet.mjs <out.jpg> <id> <lib> <t> [clip,clip,...] [view]   view: front (default) | side
// Shows library clips on one figure side by side (three.js, swiftshader) -> contact sheet for visual checks.
import { chromium } from "/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs";
import fs from "node:fs";
const R = "/Users/danielgnagi/sandboxzurich";
const [out, id, lib, t, list, view] = process.argv.slice(2);
const CLIPS = (list || "shift,shift2,look,stand2,wait,wait2,talk,listen,talk2,argue,call,text,crossed,pockets,pockets2,crossed2,sit,sit_talk,sit_chat").split(",");
const ACC = process.env.ACC ? JSON.parse(process.env.ACC) : {};
const br = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"] }); const pg = await br.newPage();
pg.on("console", (m) => { if (["error", "log"].includes(m.type())) console.log(m.text()); }); pg.on("pageerror", (e) => console.log("PAGEERR", e.message));
const MIME = { html: "text/html", js: "text/javascript", mjs: "text/javascript", glb: "model/gltf-binary", json: "application/json" };
await pg.route("http://acc.test/**", (rt) => { const f = R + new URL(rt.request().url()).pathname; if (!fs.existsSync(f)) return rt.fulfill({ status: 404, body: "" });
  rt.fulfill({ body: fs.readFileSync(f), contentType: MIME[f.split(".").pop()] || "application/octet-stream" }); });
await pg.goto("http://acc.test/pipeline/blender/check/anim_gallery.html"); await pg.waitForFunction("window.ready");
const cols = Math.min(10, CLIPS.length), rows = Math.ceil(CLIPS.length / cols), sp = process.env.ZOOM ? 0.8 : 1.0;
const items = CLIPS.map((c, i) => ({ id, lib, clip: c, t: +t, x: (i % cols) * sp, z: -(Math.floor(i / cols)) * 0, y: -Math.floor(i / cols) * 2.0, ry: view === "side" ? Math.PI / 2 : Math.PI, acc: ACC[c + "#" + i] || ACC[c] }));
const Z = process.env.ZOOM;   // ZOOM=1: close-up of head and torso (accessory fits)
const W = 1600, Hh = Z ? 500 : rows * 330 + 20, cx = (cols - 1) * sp / 2, cy = 0.9 - (rows - 1);
await pg.evaluate(([it, cam]) => window.show(it, cam), [items, Z ? { w: W, h: Hh, pos: [cx, 1.3, 2.2], look: [cx, 1.3, 0], fov: 26 } : { w: W, h: Hh, pos: [cx, cy, 11], look: [cx, cy, 0], fov: 2 * Math.atan((rows * 1.0 + 0.1) * 1.0 / 11) * 180 / Math.PI * 1.05 }]);
const buf = await pg.locator("canvas").screenshot({ type: "jpeg", quality: 82 }); fs.writeFileSync(out, buf); console.log("wrote", out, CLIPS.join(" "));
await br.close();
