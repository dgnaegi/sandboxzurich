import * as THREE from 'three';

/**
 * Road decals from the pipeline: rows [x, y, z, heading, kind]; kind 0 bike pictogram (yellow, Swiss lanes),
 * 1 manhole cover, 2 gully grate, 3 "ZONE 30" entry marking. One merged mesh per tile, atlas drawn at runtime.
 */
const SIZE: [number, number][] = [[1.3, 2.2], [0.72, 0.72], [0.55, 0.36], [2.6, 3.4]]; // width, length (m)
let atlas: THREE.Texture | null = null;

function makeAtlas(): THREE.Texture {
  const c = document.createElement('canvas'); c.width = c.height = 512;
  const g = c.getContext('2d')!;
  // 0: bicycle pictogram, yellow, drawn "lying" so it reads correctly for an approaching rider
  g.save(); g.translate(128, 128); g.strokeStyle = '#f2c200'; g.fillStyle = '#f2c200'; g.lineWidth = 9; g.lineCap = 'round';
  g.beginPath(); g.arc(0, -62, 34, 0, Math.PI * 2); g.stroke(); g.beginPath(); g.arc(0, 62, 34, 0, Math.PI * 2); g.stroke();
  g.beginPath(); g.moveTo(0, 62); g.lineTo(-10, -5); g.lineTo(18, -40); g.lineTo(0, -62); g.moveTo(-10, -5); g.lineTo(22, 10); g.lineTo(18, -40);
  g.moveTo(-14, 28); g.lineTo(-22, 28); g.moveTo(18, -40); g.lineTo(30, -46); g.stroke();
  g.beginPath(); g.arc(-34, 0, 12, 0, Math.PI * 2); g.fill(); g.restore();
  // 1: manhole cover
  g.save(); g.translate(384, 128);
  g.fillStyle = '#3b3d40'; g.beginPath(); g.arc(0, 0, 120, 0, Math.PI * 2); g.fill();
  g.strokeStyle = '#55585c'; g.lineWidth = 6;
  for (const r of [112, 80, 40]) { g.beginPath(); g.arc(0, 0, r, 0, Math.PI * 2); g.stroke(); }
  for (let a = 0; a < 12; a++) { g.beginPath(); g.moveTo(Math.cos(a * 0.524) * 40, Math.sin(a * 0.524) * 40); g.lineTo(Math.cos(a * 0.524) * 80, Math.sin(a * 0.524) * 80); g.stroke(); }
  g.restore();
  // 2: gully grate
  g.save(); g.translate(128, 384);
  g.fillStyle = '#2f3134'; g.fillRect(-120, -80, 240, 160);
  g.fillStyle = '#121314'; for (let i = -100; i <= 90; i += 24) g.fillRect(i, -64, 12, 128);
  g.restore();
  // 3: ZONE 30
  g.save(); g.translate(384, 384); g.fillStyle = '#f2f2ee'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.font = '44px Anton, sans-serif'; g.fillText('ZONE', 0, -78);
  g.font = '150px Anton, sans-serif'; g.fillText('30', 0, 30); g.restore();
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
    const cu = (kind % 2) * 0.5, cv = kind < 2 ? 0.5 : 0; // canvas row 0 = top -> v 0.5..1
    if (kind === 3) uv.push(cu + 0.5, cv, cu, cv, cu, cv + 0.5, cu + 0.5, cv + 0.5); // text reads from the approaching side
    else uv.push(cu, cv + 0.5, cu + 0.5, cv + 0.5, cu + 0.5, cv, cu, cv);
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
