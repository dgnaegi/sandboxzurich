// usage: node tests/_ray.mjs x y hdgDeg  -> what meshes the view rays hit (grid 8x5)
import { chromium } from 'playwright';
const [,, x, y, hdg] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 600 } })).newPage();
await p.goto(`http://localhost:5173/?at=${x},${y},0&t=13:00`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
await p.waitForTimeout(12000);
const out = await p.evaluate(async ([x, y, hdg]) => {
  const T = await import('/node_modules/.vite/deps/three.js');
  const cam = window.sbxCamera.clone(); const z = window.sbxTiles.ground(x, y) + 1.7;
  cam.fov = 80; cam.aspect = 4 / 3; cam.near = 0.2; cam.updateProjectionMatrix();
  cam.position.set(x, z, -y); const h = hdg * Math.PI / 180; cam.up.set(0, 1, 0);
  cam.lookAt(x + Math.sin(h), z, -(y + Math.cos(h))); cam.updateMatrixWorld(true);
  const rc = new T.Raycaster(); const res = {};
  for (let i = 0; i < 8; i++) for (let j = 0; j < 5; j++) {
    rc.setFromCamera(new T.Vector2(-0.9 + i * 0.257, -0.8 + j * 0.4), cam);
    const hit = rc.intersectObjects(window.sbxScene.children, true).find((o) => o.object.isMesh && o.object.visible);
    if (!hit) { res.none = (res.none || 0) + 1; continue; }
    let n = '', o = hit.object; while (o && n.length < 80) { n += (o.name || o.type) + '<'; o = o.parent; }
    const m = Array.isArray(hit.object.material) ? hit.object.material[0] : hit.object.material;
    if (m.type === 'ShaderMaterial' && !o) { const g = hit.object.geometry; g.computeBoundingBox(); (res.shader = res.shader || []).push([Math.round(hit.distance), g.attributes.position.count, g.boundingBox.min.toArray().map(Math.round), g.boundingBox.max.toArray().map(Math.round), Object.keys(m.uniforms || {}).slice(0, 6), hit.object.renderOrder, hit.object.position.toArray().map(Math.round), hit.point.toArray().map(Math.round)]); }
    const k = `${n} mat=${m.type}/${m.color ? m.color.getHexString() : ''} tile=${hit.object.userData?.tile ?? ''}`;
    (res[k] = res[k] || []).push(Math.round(hit.distance));
  }
  return res;
}, [Number(x), Number(y), Number(hdg)]);
console.log(JSON.stringify(out, null, 1));
await b.close();
