import * as THREE from 'three';

/** Stadt Zuerich OGD extras (CC0, public/data/ogd_extras.json from pipeline/ogd_extras.py):
 *  blue heritage plaques on the real facade (readable card when you stand close) and public bike pumps. */
interface Tafel { x: number; y: number; nx: number; ny: number; t: string; a: string; yr: string; txt: string }
interface Extras { tafeln: Tafel[]; pumps: { x: number; y: number; n: string }[] }

const UP = new THREE.Vector3(0, 1, 0);
const BLUE = new THREE.Color(0x1d4f9e), PUMP = new THREE.Color(0x2c8aa8), DARK = new THREE.Color(0x2a2f33);
const READ_R = 7;

function plateTex(): THREE.Texture {   // generic plaque face: blue, white border, title bar and text lines
  const c = document.createElement('canvas'); c.width = 128; c.height = 96;
  const g = c.getContext('2d')!;
  g.fillStyle = '#1d4f9e'; g.fillRect(0, 0, 128, 96);
  g.strokeStyle = '#f2f4f8'; g.lineWidth = 3; g.strokeRect(5, 5, 118, 86);
  g.fillStyle = '#f2f4f8'; g.fillRect(16, 16, 60, 7);
  for (let i = 0; i < 6; i++) g.fillRect(16, 34 + i * 9, 96 - (i % 3) * 14, 3);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

function card(): HTMLElement {
  let el = document.getElementById('plaque-card');
  if (el) return el;
  el = document.createElement('div'); el.id = 'plaque-card';
  el.style.cssText = 'position:fixed;left:50%;bottom:16%;transform:translateX(-50%);max-width:min(520px,90vw);z-index:8;pointer-events:none;display:none;' +
    'background:#1d4f9ee6;color:#fff;border:2px solid #f2f4f8;border-radius:6px;padding:10px 14px;font:600 14px/1.35 Barlow,sans-serif;text-shadow:0 1px 0 #0006';
  document.body.appendChild(el); return el;
}

export async function loadOgdExtras(parent: THREE.Object3D, ground: (x: number, y: number) => number): Promise<void> {
  let d: Extras;
  try { d = await (await fetch('/data/ogd_extras.json')).json(); } catch { return; }
  const g = new THREE.Group(); parent.add(g);
  const box = new THREE.BoxGeometry(1, 1, 1), plane = new THREE.PlaneGeometry(1, 1);
  const solid = new THREE.MeshLambertMaterial({ color: 0xffffff });
  const tex = plateTex(), face = new THREE.MeshBasicMaterial({ map: tex });
  const m = new THREE.Matrix4(), l = new THREE.Matrix4();
  const place = (fr: THREE.Matrix4, px: number, py: number, pz: number, sx: number, sy: number, sz: number) =>
    new THREE.Matrix4().multiplyMatrices(fr, l.multiplyMatrices(m.makeTranslation(px, py, pz), new THREE.Matrix4().makeScale(sx, sy, sz)));
  const frame = (x: number, y: number, z: number, nx: number, ny: number) => {
    const f = new THREE.Vector3(nx, 0, -ny), xa = new THREE.Vector3().crossVectors(UP, f);   // Z = outward wall normal
    return new THREE.Matrix4().makeBasis(xa, UP, f).setPosition(x, z, -y);
  };
  const body: { m: THREE.Matrix4; c: THREE.Color }[] = [];
  const faces: THREE.Matrix4[] = [];
  const tz: number[] = [];
  d.tafeln.forEach((t, i) => {
    tz[i] = ground(t.x, t.y) + 2.1;
    const fr = frame(t.x, t.y, tz[i], t.nx, t.ny);
    body.push({ m: place(fr, 0, 0, 0.015, 0.4, 0.3, 0.03), c: BLUE }); faces.push(place(fr, 0, 0, 0.033, 0.38, 0.285, 1));
  });
  for (const p of d.pumps) {
    const fr = new THREE.Matrix4().makeTranslation(p.x, ground(p.x, p.y), -p.y);
    body.push({ m: place(fr, 0, 0.55, 0, 0.12, 1.1, 0.12), c: PUMP }, { m: place(fr, 0, 1.12, 0, 0.18, 0.1, 0.18), c: DARK },
      { m: place(fr, 0.16, 1.18, 0, 0.36, 0.04, 0.05), c: DARK }, { m: place(fr, 0, 0.02, 0, 0.4, 0.04, 0.4), c: DARK });
  }
  const bm = new THREE.InstancedMesh(box, solid, body.length);
  body.forEach((b, i) => { bm.setMatrixAt(i, b.m); bm.setColorAt(i, b.c); }); bm.matrixAutoUpdate = false; g.add(bm);
  const fm = new THREE.InstancedMesh(plane, face, faces.length);
  faces.forEach((f, i) => fm.setMatrixAt(i, f)); fm.matrixAutoUpdate = false; g.add(fm);

  // reading card: poll the player position (no hook in main.ts needed); plaque within READ_R and in front of the wall
  const el = card();
  let shown = -1;
  const iv = window.setInterval(() => {
    const p = (window as unknown as { sbxPlayer?: { x: number; y: number } }).sbxPlayer;
    if (!p) return;
    let best = -1, bd = READ_R;
    d.tafeln.forEach((t, i) => {
      const dx = p.x - t.x, dy = p.y - t.y, e = Math.hypot(dx, dy);
      if (e < bd && dx * t.nx + dy * t.ny > 0) { bd = e; best = i; }
    });
    if (best === shown) return;
    shown = best;
    if (best < 0) { el.style.display = 'none'; return; }
    const t = d.tafeln[best];
    el.replaceChildren();
    const h = document.createElement('div'); h.style.cssText = 'font:20px Anton,sans-serif;letter-spacing:.5px;text-transform:uppercase';
    h.textContent = t.t || 'Blaue Tafel';
    const s = document.createElement('div'); s.style.cssText = 'opacity:.8;font-size:12px;margin-bottom:4px';
    s.textContent = [t.a, t.yr ? `Tafel ${t.yr}` : ''].filter(Boolean).join(' · ');
    const b = document.createElement('div'); b.textContent = t.txt;
    const q = document.createElement('div'); q.style.cssText = 'opacity:.7;font-size:11px;margin-top:5px';
    q.textContent = 'Quelle: Stadt Zürich, Liste der Informationstafeln an Denkmalschutzobjekten (OGD, CC0)';
    el.append(h, s, b, q); el.style.display = 'block';
  }, 250);
  g.userData.dispose = () => { window.clearInterval(iv); g.removeFromParent(); el.remove(); box.dispose(); plane.dispose(); solid.dispose(); face.dispose(); tex.dispose(); bm.dispose(); fm.dispose(); };
}
