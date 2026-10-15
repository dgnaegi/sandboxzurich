import * as THREE from 'three';

/** Entrance doors under every house number (rows [x, y, z_number, tx, ty, text]); 3 styles, one mesh per tile. */
let tex: THREE.Texture | null = null;

function atlas(): THREE.Texture {
  const c = document.createElement('canvas'); c.width = 384; c.height = 256;
  const g = c.getContext('2d')!;
  const door = (ox: number, frame: string, leaf: string, glass: boolean) => {
    g.fillStyle = frame; g.fillRect(ox, 0, 128, 256);
    g.fillStyle = leaf; g.fillRect(ox + 10, 14, 108, 242);
    if (glass) { g.fillStyle = '#2c3a46'; g.fillRect(ox + 22, 30, 84, 110); g.strokeStyle = leaf; g.lineWidth = 6; g.strokeRect(ox + 22, 30, 84, 110); g.beginPath(); g.moveTo(ox + 64, 30); g.lineTo(ox + 64, 140); g.stroke(); }
    g.strokeStyle = 'rgba(0,0,0,0.35)'; g.lineWidth = 3; g.strokeRect(ox + 22, 155, 84, 85);
    g.fillStyle = '#c9b46a'; g.fillRect(ox + 100, 150, 8, 22); // handle
    g.fillStyle = '#9a968c'; g.fillRect(ox, 0, 128, 12); // lintel
  };
  door(0, '#d8d2c4', '#6b4a30', true);    // wooden door with glass, plaster frame
  door(128, '#cfcabe', '#2f4a3a', true);  // dark green
  door(256, '#9aa0a6', '#8d969e', false); // modern metal/glass
  g.fillStyle = '#5a6670'; g.fillRect(256 + 22, 30, 84, 200);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return t;
}

export function buildDoors(rows: (number | string)[][]): THREE.Object3D[] {
  if (!rows.length) return [];
  tex ??= atlas();
  const pos: number[] = [], uv: number[] = [], nrm: number[] = [], idx: number[] = [];
  const step: number[] = [], sidx: number[] = [];
  for (const r of rows) {
    const [x, y, zn, tx, ty] = r as number[];
    const ox = ty, oy = -tx, z0 = zn - 2.2, b = pos.length / 3, hw = 0.6, h = 2.3, off = 0.03;
    const style = Math.abs(Math.floor(x * 7 + y * 3)) % 3;
    for (const [u, v] of [[-hw, 0], [hw, 0], [hw, h], [-hw, h]]) {
      pos.push(x + ox * off + tx * u, z0 + v, -(y + oy * off + ty * u)); nrm.push(ox, 0, -oy);
    }
    uv.push(style / 3, 0, (style + 1) / 3, 0, (style + 1) / 3, 1, style / 3, 1);
    idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
    // stone step in front of the door
    const sb = step.length / 3, d = 0.35, sh = 0.12;
    for (const [u, w, zz] of [[-0.75, 0, sh], [0.75, 0, sh], [0.75, d, sh], [-0.75, d, sh], [-0.75, d, 0], [0.75, d, 0]]) {
      step.push(x + tx * u + ox * w, z0 + zz, -(y + ty * u + oy * w));
    }
    sidx.push(sb, sb + 2, sb + 1, sb, sb + 3, sb + 2, sb + 3, sb + 4, sb + 5, sb + 3, sb + 5, sb + 2);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  const s = new THREE.BufferGeometry();
  s.setAttribute('position', new THREE.Float32BufferAttribute(step, 3));
  s.setIndex(sidx); s.computeVertexNormals();
  return [new THREE.Mesh(g, new THREE.MeshLambertMaterial({ map: tex })),
    new THREE.Mesh(s, new THREE.MeshLambertMaterial({ color: 0x9c978c, side: THREE.DoubleSide }))];
}
