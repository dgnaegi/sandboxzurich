import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Tram/bus stops from public/data/transit.json: VBZ-style stop pole (name + lines) and a glass shelter. */
interface LineJson { ref: string; mode: string; pts: number[][]; stops: { name: string; s: number }[] }

function panel(name: string, lines: string[]): THREE.Texture {
  const c = document.createElement('canvas'); c.width = 256; c.height = 256;
  const g = c.getContext('2d')!;
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 256, 256);
  g.fillStyle = '#16a34a'; g.beginPath(); g.arc(128, 62, 52, 0, Math.PI * 2); g.fill();   // generic green stop disc with H shape
  g.fillStyle = '#ffffff'; g.fillRect(100, 34, 12, 56); g.fillRect(144, 34, 12, 56); g.fillRect(100, 56, 56, 12);
  g.fillStyle = '#111'; g.textAlign = 'center';
  const fit = Math.min(30, (240 / Math.max(1, (g.font = '700 30px "Barlow Condensed", sans-serif', g.measureText(name).width))) * 30);
  g.font = `700 ${fit}px "Barlow Condensed", sans-serif`; g.fillText(name, 128, 140);
  lines.slice(0, 5).forEach((l, i, a) => {
    const x = 128 + (i - (a.length - 1) / 2) * 48;
    g.fillStyle = '#1f6db6'; g.fillRect(x - 20, 168, 40, 40);
    g.fillStyle = '#fff'; g.font = '26px Anton, sans-serif'; g.fillText(l, x, 199);
  });
  g.fillStyle = '#d8dde2'; g.fillRect(0, 236, 256, 20);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** Passenger information display (dark LED box: next departures as orange text). */
function infoTex(lines: string[]): THREE.Texture {
  const c = document.createElement('canvas'); c.width = 128; c.height = 64;
  const g = c.getContext('2d')!;
  g.fillStyle = '#07090c'; g.fillRect(0, 0, 128, 64);
  g.fillStyle = '#ffb347'; g.font = 'bold 15px monospace'; g.textAlign = 'left';
  lines.slice(0, 3).forEach((l, i) => { g.fillText(`${l.padEnd(3)} ${2 + i * 4 + (l.length * 3) % 5} min`, 8, 18 + i * 19); });
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

const grey = new THREE.MeshLambertMaterial({ color: 0x8a9095 });
const glass = new THREE.MeshLambertMaterial({ color: 0x9fb8c8, transparent: true, opacity: 0.35, depthWrite: false });
const roofMat = new THREE.MeshLambertMaterial({ color: 0x5f666b });

export function buildStops(data: { lines: LineJson[] }, ground: (x: number, y: number) => number): THREE.Group {
  const group = new THREE.Group();
  const byName = new Map<string, { x: number; y: number; h: number; lines: Set<string> }[]>();
  for (const l of data.lines) for (const st of l.stops) {
    let s = st.s;
    for (let i = 0; i + 1 < l.pts.length; i++) {
      const [ax, ay] = l.pts[i], [bx, by] = l.pts[i + 1], L = Math.hypot(bx - ax, by - ay);
      if (s > L) { s -= L; continue; }
      const t = s / L, x = ax + (bx - ax) * t, y = ay + (by - ay) * t, h = Math.atan2(bx - ax, by - ay);
      const px = x + Math.cos(h) * 2.6, py = y - Math.sin(h) * 2.6; // right-hand platform edge
      const list = byName.get(st.name) ?? byName.set(st.name, []).get(st.name)!;
      const near = list.find((e) => Math.hypot(e.x - px, e.y - py) < 15);
      if (near) near.lines.add(l.ref); else list.push({ x: px, y: py, h, lines: new Set([l.ref]) });
      break;
    }
  }
  for (const [name, list] of byName) for (const st of list) {
    const z = ground(st.x, st.y), o = new THREE.Group();
    o.position.set(st.x, z, -st.y); o.rotation.y = -st.h;
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 2.9, 6).translate(0, 1.45, 0), grey);
    // two faces back to back: a DoubleSide plane shows the name mirrored from behind
    const signMat = new THREE.MeshLambertMaterial({ map: panel(name, [...st.lines].sort()) });
    const sign = new THREE.Group();
    sign.add(new THREE.Mesh(new THREE.PlaneGeometry(0.6, 0.6).translate(0, 2.5, 0.006), signMat),
      new THREE.Mesh(new THREE.PlaneGeometry(0.6, 0.6).rotateY(Math.PI).translate(0, 2.5, -0.006), signMat));
    sign.rotation.y = Math.PI / 2;
    pole.position.x = sign.position.x = 0.4;
    // shelter: roof, back glass, two posts, bench
    const frame = mergeGeometries([
      new THREE.BoxGeometry(0.06, 2.4, 0.06).translate(1.4, 1.2, -1.6), new THREE.BoxGeometry(0.06, 2.4, 0.06).translate(1.4, 1.2, 1.6),
      new THREE.BoxGeometry(1.4, 0.06, 0.4).translate(1.6, 0.45, 0).rotateY(0),
    ].map((g) => g.toNonIndexed()))!;
    const roof = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.08, 3.6).translate(1.3, 2.45, 0), roofMat);
    const back = new THREE.Mesh(new THREE.BoxGeometry(0.03, 2.0, 3.2).translate(1.75, 1.25, 0), glass);
    const info = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.25).translate(1.72, 1.7, -1.0),
      new THREE.MeshBasicMaterial({ map: infoTex([...st.lines].sort()) }));
    info.rotation.y = 0; info.position.x = 0; info.rotateY(-Math.PI / 2); info.position.set(-0.01, 0, 0);
    o.add(info, pole, sign, new THREE.Mesh(frame, grey), roof, back);
    group.add(o);
  }
  return group;
}
