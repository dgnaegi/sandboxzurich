// Contact sheet of all car types: near (drive rig, physical materials) and medium (traffic/parked instanced material).
// Output preview/cars_v3.jpg (or argv[2]); argv[3] = comma list of types.
import { chromium } from 'playwright';
import { execSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
const BASE = process.env.BASE || 'http://localhost:5173';
const out = new URL('../../preview/', import.meta.url).pathname, tmp = '/tmp/csheet/';
const BIG = types0().length <= 2;
function types0() { return (process.argv[3] || 'x,x,x').split(','); }
const BIGD = process.env.D ? Number(process.env.D) : null;
const name = process.argv[2] || 'cars_v3.jpg';
const types = (process.argv[3] || 'hatch,wagon,small,sedan,csuv,suv,van,taxi,sport').split(',');
mkdirSync(tmp, { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const page = await (await b.newContext({ viewport: { width: BIG ? 800 : 640, height: BIG ? 500 : 400 } })).newPage();
page.on('pageerror', (e) => { if (!/arc'/.test(e.message)) console.log('pageerror', e.message); });
page.on('console', (m) => { if (m.type() === 'error' || /shader|THREE.WebGLProgram/i.test(m.text())) console.log('console', m.text().slice(0, 600)); });
await page.goto(`${BASE}/?at=785,-635,0.37&t=15:30&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
await page.waitForTimeout(1500);
await page.addStyleTag({ content: 'body > *:not(canvas) { display: none !important; }' });
await page.evaluate(() => { window.sbxPlayer.update = () => {}; window.sbxPlayer.mesh.visible = false; window.sbxScene.traverse((o) => { if (o.isSkinnedMesh) o.visible = false; }); });
const colors = [0x8c1c22, 0xe2e2df, 0x1b2c4e, 0x5d6268, 0x24402f, 0x1a1c20, 0xf2f2ef, 0xf2f2ef, 0xf2c200];
for (let i = 0; i < types.length; i++) for (const mode of ['near', 'mid']) {
  await page.evaluate(async ([type, col, i, mode, BIGD]) => {
    const { buildRig } = await import('/src/player/vehicle_model.ts');
    const cu = performance.getEntriesByType('resource').map((e) => e.name).find((n) => /\/src\/world\/cars\.ts/.test(n));
    const { CAR_GEO, carMaterial } = await import(cu);
    const p = window.sbxPlayer, sc = window.sbxScene;
    sc.getObjectByName('sheetcar')?.removeFromParent();
    const color = new sc.fog.color.constructor(col);
    const x = p.x + 2.5, y = p.y + 5, z = window.sbxTiles.groundAt(x, y, window.sbxTiles.ground(x, y));
    let obj;
    if (mode === 'near') { const rig = await buildRig(type, color); obj = rig.group; rig.setWheels(0.5, 0.2); rig.setLights({ brake: i % 3 === 0, reverse: false, night: 0, blink: 0, blinkOn: false }); }
    else {
      let IM = null; sc.traverse((o) => { if (!IM && o.isInstancedMesh) IM = o.constructor; });
      const im = new IM(CAR_GEO[type], carMaterial, 1);
      im.setMatrixAt(0, sc.matrix.clone().identity()); im.setColorAt(0, color); obj = im; im.frustumCulled = false;
    }
    obj.name = 'sheetcar'; obj.position.set(x, z, -y); obj.rotation.y = 0;
    sc.add(obj);
    const c = window.sbxCamera, d = mode === 'near' ? (BIGD ?? 0.78) : 1.9, back = i % 4 === 3, sx = back ? -1 : 1;
    c.position.set(x + sx * 3.2 * d, z + (mode === 'near' ? 1.1 : 1.9), -y - sx * 4.6 * d); c.lookAt(x, z + 0.55, -y);
    window.__dbg = [obj.geometry?.attributes.position.count, obj.count, obj.material?.type, obj.visible, !!obj.parent, c.position.toArray(), obj.position.toArray()];
  }, [types[i], colors[i % colors.length], i, mode, BIGD]);
  await page.waitForTimeout(450);
  if (mode === 'mid' && i === 0) console.log(JSON.stringify(await page.evaluate(() => window.__dbg)));
  await page.screenshot({ path: `${tmp}${i}${mode}.png` });
}
await b.close();
const T = BIG ? [800, 500, 2] : [400, 250, 4];
execSync(`python3 - <<'PY'
from PIL import Image
n=${types.length}
tw,th,cols=${T[0]},${T[1]},${T[2]}
rows=(n*2+cols-1)//cols
W=Image.new('RGB',(tw*cols, th*rows))
k=0
for i in range(n):
    for m in ('near','mid'):
        im=Image.open(f'${tmp}{i}{m}.png').resize((tw,th)); W.paste(im,((k%cols)*tw,(k//cols)*th)); k+=1
W.save('${out}${name}',quality=84)
PY`);
console.log('ok');
