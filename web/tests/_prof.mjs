// usage: node tests/_prof.mjs routeIndexOrName kind fromS toS step
import { chromium } from 'playwright';
import fs from 'node:fs';
const [name, kind, s0, s1, st] = process.argv.slice(2);
const R = JSON.parse(fs.readFileSync('../logs/bridge_routes.json')).find((r) => r.name.includes(name) && r.kind === kind);
const b=await chromium.launch({args:['--use-gl=angle']});const p=await (await b.newContext({viewport:{width:640,height:360}})).newPage();
await p.goto(`http://localhost:5173/?at=${R.pts[0][0]},${R.pts[0][1]},0&t=12:00&nopost`);await p.waitForFunction(()=>window.sbxReady,null,{timeout:60000});await p.waitForTimeout(2000);
const out=await p.evaluate(async({pts,s0,s1,st})=>{const T=window.sbxTiles;const cum=[0];for(let i=1;i<pts.length;i++)cum.push(cum[i-1]+Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]));
const at=(s)=>{let i=1;while(i<cum.length-1&&cum[i]<s)i++;const t=(s-cum[i-1])/(cum[i]-cum[i-1]||1);return [pts[i-1][0]+(pts[i][0]-pts[i-1][0])*t,pts[i-1][1]+(pts[i][1]-pts[i-1][1])*t]};
const o=[];let z=null;for(let s=+s0;s<=+s1;s+=+st){const [x,y]=at(s);await T.update(x,y);const g=T.ground(x,y);if(z===null)z=g;const d=T.bridges.heightAt(x,y,z,1.5);const ga=T.groundAt(x,y,z);o.push(`${s.toFixed(0)} (${x.toFixed(0)},${y.toFixed(0)}) g=${g.toFixed(2)} deck=${d==null?'-':d.toFixed(2)} ga=${ga.toFixed(2)}`);z=ga}return o.join('\n')},{pts:R.pts,s0,s1,st});
console.log(out);await b.close()
