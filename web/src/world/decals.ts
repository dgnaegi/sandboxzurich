import * as THREE from 'three';

/**
 * Road decals from the pipeline: rows [x, y, z, heading, kind]; kind 0 bike pictogram (yellow, Swiss lanes),
 * 1 manhole cover, 2 gully grate, 3 "ZONE 30" entry marking, 4 straight arrow, 5 BUS, 6 painted 30 roundel, 7 left, 8 right, 9 straight+left, 10 straight+right arrow. One merged mesh per tile, atlas drawn at runtime.
 */
const SIZE: [number, number][] = [[1.0, 1.9], [0.72, 0.72], [0.55, 0.36], [2.6, 3.4], [1.4, 4.2], [1.7, 3.0], [1.8, 1.8], [1.7, 4.2], [1.7, 4.2], [2.2, 4.2], [2.2, 4.2]]; // width, length (m)
const COLS = 4, ROWS = 4;
let atlas: THREE.Texture | null = null;

function makeAtlas(): THREE.Texture {
  const c = document.createElement('canvas'); c.width = 1024; c.height = 1024;
  const g = c.getContext('2d')!;
  // 0: Swiss bicycle pictogram (yellow line drawing, side view, rider facing right). Canvas top = far end (driving direction);
  // the quad is stretched along the road (foreshortened view), so the wheels sit side by side across the lane.
  g.save(); g.translate(128, 128); g.strokeStyle = '#f2c200'; g.fillStyle = '#f2c200'; g.lineWidth = 11; g.lineCap = 'round'; g.lineJoin = 'round';
  const R = [-62, 56], F = [62, 56], BB = [-6, 56], S = [-28, 4], T = [40, 2];
  g.beginPath(); g.arc(R[0], R[1], 40, 0, Math.PI * 2); g.stroke(); g.beginPath(); g.arc(F[0], F[1], 40, 0, Math.PI * 2); g.stroke();
  g.beginPath(); g.moveTo(R[0], R[1]); g.lineTo(BB[0], BB[1]); g.lineTo(S[0], S[1]); g.lineTo(R[0], R[1]);
  g.moveTo(BB[0], BB[1]); g.lineTo(T[0], T[1]); g.lineTo(S[0], S[1]); g.moveTo(F[0], F[1]); g.lineTo(T[0] + 6, T[1] - 14); g.lineTo(T[0] - 2, T[1] - 24); g.lineTo(T[0] + 22, T[1] - 24);
  g.moveTo(S[0], S[1]); g.lineTo(S[0] - 6, S[1] - 8); g.stroke();
  g.lineWidth = 14; g.beginPath(); g.moveTo(S[0] - 6, S[1] - 12); g.lineTo(16, -58); g.lineTo(T[0] + 18, T[1] - 26); g.stroke(); // torso + arm
  g.beginPath(); g.moveTo(S[0] - 6, S[1] - 12); g.lineTo(14, 26); g.lineTo(BB[0] + 4, BB[1] + 4); g.stroke(); // leg
  g.beginPath(); g.arc(24, -86, 17, 0, Math.PI * 2); g.fill(); g.restore();
  // 1: manhole cover
  g.save(); g.translate(384, 128);
  g.fillStyle = '#3b3d40'; g.beginPath(); g.arc(0, 0, 120, 0, Math.PI * 2); g.fill();
  g.strokeStyle = '#55585c'; g.lineWidth = 6;
  for (const r of [112, 80, 40]) { g.beginPath(); g.arc(0, 0, r, 0, Math.PI * 2); g.stroke(); }
  for (let a = 0; a < 12; a++) { g.beginPath(); g.moveTo(Math.cos(a * 0.524) * 40, Math.sin(a * 0.524) * 40); g.lineTo(Math.cos(a * 0.524) * 80, Math.sin(a * 0.524) * 80); g.stroke(); }
  g.restore();
  // 2: gully grate
  g.save(); g.translate(640, 128);
  g.fillStyle = '#2f3134'; g.fillRect(-120, -80, 240, 160);
  g.fillStyle = '#121314'; for (let i = -100; i <= 90; i += 24) g.fillRect(i, -64, 12, 128);
  g.restore();
  // 3: ZONE 30
  g.save(); g.translate(896, 128); g.fillStyle = '#f2f2ee'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.font = '44px Anton, sans-serif'; g.fillText('ZONE', 0, -78);
  g.font = '150px Anton, sans-serif'; g.fillText('30', 0, 30); g.restore();
  // arrows (white, canvas up = driving direction): 4 straight, 7 left, 8 right, 9 straight+left, 10 straight+right
  const head = (x: number, y: number, ang: number) => { g.save(); g.translate(x, y); g.rotate(ang); g.beginPath(); g.moveTo(0, -40); g.lineTo(46, 20); g.lineTo(-46, 20); g.closePath(); g.fill(); g.restore(); };
  const arrow = (cx: number, cy: number, dirs: ('f' | 'l' | 'r')[]) => {
    g.save(); g.translate(cx, cy); g.fillStyle = '#f2f2ee'; g.strokeStyle = '#f2f2ee'; g.lineWidth = 26; g.lineCap = 'butt'; g.lineJoin = 'miter';
    const turn = dirs.find((d) => d !== 'f'); const sgn = turn === 'l' ? -1 : 1; const straight = dirs.includes('f');
    if (straight) { g.beginPath(); g.moveTo(0, 118); g.lineTo(0, -64); g.stroke(); head(0, -88, 0); }
    if (turn) {
      const by = straight ? 50 : 10;
      if (!straight) { g.beginPath(); g.moveTo(0, 118); g.lineTo(0, by); g.stroke(); }
      g.beginPath(); g.moveTo(0, by + 13); g.lineTo(0, by); g.lineTo(sgn * 70, by - 70); g.stroke(); head(sgn * 88, by - 88, sgn * Math.PI / 4);
    }
    g.restore();
  };
  arrow(128, 384, ['f']); arrow(896, 384, ['l']); arrow(128, 640, ['r']); arrow(384, 640, ['f', 'l']); arrow(640, 640, ['f', 'r']);
  // 5: BUS lettering
  g.save(); g.translate(384, 384); g.fillStyle = '#f2f2ee'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = '110px Anton, sans-serif'; g.fillText('BUS', 0, 0); g.restore();
  // 6: "30" roundel painted (Tempo 30 on the road)
  g.save(); g.translate(640, 384); g.strokeStyle = '#f2f2ee'; g.lineWidth = 18; g.beginPath(); g.arc(0, 0, 96, 0, Math.PI * 2); g.stroke();
  g.fillStyle = '#f2f2ee'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = '110px Anton, sans-serif'; g.fillText('30', 0, 6); g.restore();
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}

export function buildDecals(rows: number[][]): THREE.Object3D[] {
  if (!rows.length) return [];
  atlas ??= makeAtlas();
  const pos: number[] = [], uv: number[] = [], nrm: number[] = [], idx: number[] = [];
  for (const [x, y, z, h, kind] of rows) {
    const [w, l] = SIZE[kind] ?? SIZE[1];
    const fx = Math.sin(h), fy = Math.cos(h), rx = Math.cos(h), ry = -Math.sin(h); // forward / right in local metres
    const b = pos.length / 3;
    for (const [u, v] of [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]]) {
      const px = x + rx * u * w + fx * v * l, py = y + ry * u * w + fy * v * l;
      pos.push(px, z, -py); nrm.push(0, 1, 0);
    }
    // canvas top (v high) = far end = driving direction; canvas left = driver's left
    const cw = 1 / COLS, ch = 1 / ROWS, cu = (kind % COLS) * cw, cv = (ROWS - 1 - Math.floor(kind / COLS)) * ch;
    uv.push(cu, cv, cu + cw, cv, cu + cw, cv + ch, cu, cv + ch);
    idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  const m = new THREE.MeshLambertMaterial({ map: atlas, alphaTest: 0.4, transparent: false, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3 });
  const mesh = new THREE.Mesh(g, m);
  mesh.receiveShadow = true;
  return [mesh];
}
