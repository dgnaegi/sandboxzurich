import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { Heights, type HeightData } from './heights';
import { buildLandmarks, type LandmarkRow } from '../world/landmarks';
import { buildPlaygrounds, type PlaygroundRow } from '../world/playgrounds';
import { buildBridges, BridgeIndex, type BridgeRows } from '../world/bridges';
import { loadWorldMaterial } from './materials';
import { Colliders } from '../player/collision';
import { buildProps, type PropMeta } from '../world/props';
import { treeField } from '../world/tree_field';
import type { Bikes } from '../world/bikes';
import { buildGraffiti, buildPosters, buildSigns, buildWildPosters, type Sign } from '../world/signs';
import { buildHouseNumbers, buildStreetSigns } from '../world/streetsigns';
import { buildDecals } from '../world/decals';
import { buildPlaces, type PlaceMeta } from '../world/places_detail';
import { buildRooftops, type RoofChunk, type RoofRow } from '../world/rooftops';
import { buildDetails, type DetailMeta } from '../world/details';
import { buildYards, type YardMeta } from '../world/yards'; // YARDS
import { buildDoors } from '../world/doors';
import { buildConstruction, buildCranes, buildFence, buildScooters, buildSites } from '../world/construction';
import { parkedCars } from '../world/parkedcars';
import { purgeLights } from '../world/night_lights';
import { forgetSignMat } from '../world/signs';
import { buildAFrames, buildSacks, sackGroups } from '../world/streetlife';
import { buildTrafficSigns, buildSignals, purgeSignals } from '../world/trafficsigns';
import { attachKnocks, knockKey } from '../world/knockable';
import { waterMaterial, disposeWater, type WaterMeta } from '../world/water'; // water

interface TileRef { name: string; ix: number; iy: number }
export interface Place { name: string; sub: string; x: number; y: number; yaw: number }
export interface World { tile: number; area: number[]; polygon?: number[][]; tiles: TileRef[]; heights: HeightData; places?: Place[] }
interface Mask { x0: number; y0: number; n: number; res: number; depth: number; bits: string }
interface TileMeta extends PropMeta { colliders: number[][][]; signs: Sign[]; posters: number[][]; wild?: number[][]; paths: number[][][]; mask: Mask }

const BASE = (import.meta.env.VITE_TILE_BASE_URL as string | undefined) ?? '/tiles';
const LOAD_RADIUS_PC = 450, LOAD_RADIUS_PHONE = 280; // phones: fewer tiles in memory (iOS Safari tab limit)
const UNLOAD_EXTRA = 200, UNLOAD_EXTRA_PHONE = 110;

/** Loads tiles around the player, registers colliders, exposes ground height incl. lowered carriageways. */
export class Tiles {
  readonly heights: Heights;
  readonly colliders = new Colliders();
  readonly bridges = new BridgeIndex();
  onPaths: (p: number[][][]) => void = () => {};
  onLawn: (rows: number[][]) => void = () => {};
  onFountains: (rows: number[][]) => void = () => {};
  onSchools: (rows: number[][]) => void = () => {};
  onSpots: (meta: never) => void = () => {};
  private loaded = new Map<string, THREE.Group | null>();
  private props = new Map<string, { g: THREE.Group; near: THREE.Group; far: THREE.Group; bikes: THREE.Object3D[]; lods: THREE.Object3D[]; roofs: RoofChunk[]; x: number; y: number }>();
  roofRadius = 250; // rooftop furniture (dormers, PV, units): chunks beyond this are hidden
  bikes: Bikes | null = null;
  treeRadius = 170;
  bikeRadius = 150;
  private seen = new Set<string>(); // colliders/paths registered once per tile
  private hmaps = new Map<string, Heights>();
  private waters = new Map<string, THREE.Mesh[]>();  // water surfaces per tile (inWater queries)
  private masks = new Map<string, { m: Mask; bytes: Uint8Array }>();
  private loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);

  private constructor(readonly world: World, private scene: THREE.Scene, private shadows: boolean, readonly mat: THREE.Material) {
    this.heights = new Heights(world.heights);
    scene.add(treeField.group);
  }

  static async load(scene: THREE.Scene, shadows: boolean, anisotropy: number): Promise<Tiles> {
    const [world, mat] = await Promise.all([
      fetch(`${BASE}/world.json`).then((r) => r.json() as Promise<World>),
      loadWorldMaterial('/tex', anisotropy, shadows)   // shadows = desktop tier = PBR + IBL,
    ]);
    const t = new Tiles(world, scene, shadows, mat);
    // station platforms and stairs as walkable decks (pipeline/landmarks/st_station.py); optional file
    try { const r = await fetch('/data/station_decks.json'); if (r.ok) t.bridges.add(await r.json() as BridgeRows, 'stations'); } catch { /* no station decks */ }
    // Zuerich HB: raised platforms 3-18 (pipeline/landmarks/hb_perron.py); optional file
    try { const r = await fetch('/data/hb3_decks.json'); if (r.ok) t.bridges.add(await r.json() as BridgeRows, 'hb3'); } catch { /* hb3: no underground decks */ }
    try { const r = await fetch('/data/velotunnel_decks.json'); if (r.ok) t.bridges.add(await r.json() as BridgeRows, 'velotunnel'); } catch { /* no velotunnel decks */ }   // velotunnel (pipeline/landmarks/velotunnel.py)
    try { const r = await fetch('/data/hb_decks.json'); if (r.ok) t.bridges.add(await r.json() as BridgeRows, 'hb'); } catch { /* no HB decks */ }
    return t;
  }

  get area() { return this.world.area; }

  /** Inside the playable polygon (the fence)? */
  inPlay(x: number, y: number): boolean {
    const r = this.world.polygon;
    if (!r) { const a = this.world.area; return x > a[0] && x < a[2] && y > a[1] && y < a[3]; }
    let c = false;
    for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
      const [xi, yi] = r[i], [xj, yj] = r[j];
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
    }
    return c;
  }

  /** Bridge deck within reach of height z, else the ground. */
  groundAt(x: number, y: number, z: number): number {
    const g = this.ground(x, y), d = this.bridges.heightAt(x, y, z, 1.5, 1.0);
    if (d === null) return g;
    if (this.bridges.lastSub) return d;   // hb3: underground deck (Shopville, Loewenstrasse, Museumstrasse) below the terrain
    const e = d - g;                        // deck above the terrain: fades in over the first 0.35 m so ramp ends join the road without a step
    if (e >= 0.35) return d;
    if (e <= 0) return g;
    const k = e / 0.35;
    return g + e * k * k * (3 - 2 * k);
  }

  /** Is the body at (x, y, z) on an elevated deck (> 2.5 m above the ground below)? Ground footprints (buildings) must not block it. */
  onElevatedDeck(x: number, y: number, z: number): boolean {
    const d = this.bridges.heightAt(x, y, z, 1.0, 1.0);
    return d !== null && d - this.ground(x, y) > 2.5;
  }

  /** Body collision at height z: footprints (unless on an elevated deck) and the deck railings. */
  resolveBody(x: number, y: number, rad: number, z: number): [number, number] {
    if (!this.onElevatedDeck(x, y, z)) [x, y] = this.colliders.resolve(x, y, rad);
    return this.bridges.railPush(x, y, z, rad);
  }

  /** Walking/cycling collision: footprints, then trunks/poles/benches (circles). Parked cars are car-sized footprints from the pipeline already. */
  resolveSolid(x: number, y: number, rad: number, z?: number): [number, number] {
    const up = z !== undefined && this.onElevatedDeck(x, y, z);   // on a bridge: the buildings below do not count
    if (!up) { [x, y] = this.colliders.resolve(x, y, rad); [x, y] = this.colliders.resolveCircles(x, y, rad); }
    return [x, y];
  }

  /** Is local (x, y) on a carriageway (lowered kerb mask)? */
  onRoad(x: number, y: number): boolean {
    const s = this.world.tile, e = this.masks.get(`t_${Math.floor(x / s)}_${Math.floor(y / s)}`);
    if (!e) return false;
    const cx = Math.floor((x - e.m.x0) / e.m.res), cy = Math.floor((y - e.m.y0) / e.m.res), i = cy * e.m.n + cx;
    return cx >= 0 && cy >= 0 && cx < e.m.n && ((e.bytes[i >> 3] >> (7 - (i & 7))) & 1) === 1;
  }

  /** Is local (x, y) over a river/lake surface? (vertical ray against the loaded water meshes) */
  inWater(x: number, y: number): boolean {
    const s = this.world.tile, ms = this.waters.get(`t_${Math.floor(x / s)}_${Math.floor(y / s)}`);
    if (!ms?.length) return false;
    const rc = new THREE.Raycaster(new THREE.Vector3(x, 500, -y), new THREE.Vector3(0, -1, 0), 0, 1000);
    const sides = ms.map((m) => (m.material as THREE.Material).side);
    ms.forEach((m) => { (m.material as THREE.Material).side = THREE.DoubleSide; });
    const hit = rc.intersectObjects(ms, false).length > 0;
    ms.forEach((m, i) => { (m.material as THREE.Material).side = sides[i]; });
    return hit;
  }

  /** Solid tile geometry (decks, bridges, roofs) within `h` metres above feet height z at (x, y)? (up-ray against the tile's bridge meshes) */
  ceilingAbove(x: number, y: number, z: number, h: number): boolean {
    const s = this.world.tile, g = this.loaded.get(`t_${Math.floor(x / s)}_${Math.floor(y / s)}`);
    if (!g) return false;
    const ms: THREE.Mesh[] = [];
    g.traverse((o) => { const m = o as THREE.Mesh; if (m.isMesh && !(o as THREE.InstancedMesh).isInstancedMesh && o.visible) ms.push(m); });
    const sides = ms.map((m) => (m.material as THREE.Material).side);
    ms.forEach((m) => { (m.material as THREE.Material).side = THREE.DoubleSide; });
    const rc = new THREE.Raycaster(new THREE.Vector3(x, z + 1.0, -y), new THREE.Vector3(0, 1, 0), 0, h);
    const hit = rc.intersectObjects(ms, false).length > 0;
    ms.forEach((m, i) => { (m.material as THREE.Material).side = sides[i]; });
    return hit;
  }

  /** Walkable ground height at local (x, y): terrain minus the kerb drop on carriageways. */
  ground(x: number, y: number): number {
    const s = this.world.tile, k = `t_${Math.floor(x / s)}_${Math.floor(y / s)}`;
    const e = this.masks.get(k);
    let z = (this.hmaps.get(k) ?? this.heights).at(x, y); // exact 2 m tile map, else the coarse 8 m grid
    if (e) {
      const cx = Math.floor((x - e.m.x0) / e.m.res), cy = Math.floor((y - e.m.y0) / e.m.res), i = cy * e.m.n + cx;
      if (cx >= 0 && cy >= 0 && cx < e.m.n && (e.bytes[i >> 3] >> (7 - (i & 7))) & 1) z -= e.m.depth;
    }
    return z;
  }

  /** Hide props (cars, trees, signs …) of tiles whose centre is farther than `radius`. Cheap, call per frame. */
  cull(x: number, y: number, radius: number) {
    treeField.update(x, y);
    for (const p of this.props.values()) {
      const d = Math.hypot(p.x - x, p.y - y);
      p.g.visible = d < radius;
      p.near.visible = d < this.treeRadius;   // full leaf-card trees close by
      p.far.visible = d >= this.treeRadius;   // cheap blobs further away (fog hides the rest)
      for (const c of p.roofs) c.g.visible = Math.hypot(c.x - x, c.y - y) < this.roofRadius;
      const hi = d < this.bikeRadius;          // detailed bikes/cars only in the nearest tiles, stand-ins beyond
      for (const b of p.lods) { b.visible = hi; (b.userData.lo as THREE.Object3D).visible = !hi; }
    }
  }

  /** Load tiles whose centre is within LOAD_RADIUS of local (x, y). Resolves when all are in. */
  async update(x: number, y: number): Promise<void> {
    const s = this.world.tile, jobs: Promise<void>[] = [];
    for (const t of this.world.tiles) {
      if (Math.hypot((t.ix + 0.5) * s - x, (t.iy + 0.5) * s - y) < (this.shadows ? LOAD_RADIUS_PC : LOAD_RADIUS_PHONE) && !this.loaded.has(t.name)) {
        this.loaded.set(t.name, null);
        jobs.push(this.loadTile(t).catch((err) => { console.warn('tile failed', t.name, err); })); // a missing tile must not block jumps (stays marked, no retry)
      }
    }
    let purged = false;
    // free GPU memory of far tiles (important on phones); colliders and masks stay (small)
    for (const [name, g] of this.loaded) {
      const t = this.props.get(name);
      if (!g || !t || Math.hypot(t.x - x, t.y - y) < (this.shadows ? LOAD_RADIUS_PC + UNLOAD_EXTRA : LOAD_RADIUS_PHONE + UNLOAD_EXTRA_PHONE)) continue;
      this.scene.remove(g);
      this.disposeTile(g);
      for (const b of t.bikes) this.bikes?.forget(b);
      g.traverse((o) => sackGroups.delete(o));
      this.loaded.delete(name);
      this.props.delete(name);
      this.bridges.remove(name);
      treeField.remove(name);
      this.waters.delete(name);
      this.colliders.removeCircles(name); this.colliders.removeCircles(knockKey(name));
      purged = true;
    }
    if (purged) { parkedCars.purge(); purgeLights(); purgeSignals(); }
    await Promise.all(jobs);
  }

  /** Free GPU + CPU resources of a removed tile group: geometries, materials (except the shared world material), their textures. */
  private disposeTile(root: THREE.Object3D) {
    root.traverse((o) => {
      const m = o as THREE.Mesh;
      if ((o as THREE.InstancedMesh).isInstancedMesh) (o as THREE.InstancedMesh).dispose();
      if (!m.isMesh && !(m as unknown as THREE.Line).isLine && !(m as unknown as THREE.Points).isPoints) return;
      m.geometry?.dispose();
      const mats = Array.isArray(m.material) ? m.material : m.material ? [m.material] : [];
      for (const mat of mats) {
        if (mat === this.mat) continue;
        if (mat.userData?.tex) { disposeWater(mat); continue; } // water shader material
        forgetSignMat(mat);
        for (const v of Object.values(mat)) if ((v as THREE.Texture | undefined)?.isTexture) (v as THREE.Texture).dispose(); // shared ones are simply re-uploaded when drawn again
        mat.dispose();
      }
    });
  }

  private async loadTile(t: TileRef) {
    const [gltf, meta] = await Promise.all([
      this.loader.loadAsync(`${BASE}/${t.name}.glb`),
      fetch(`${BASE}/${t.name}.json`).then((r) => r.json() as Promise<TileMeta>),
    ]);
    const g = gltf.scene;
    const firstLoad = !this.seen.has(t.name);
    if (firstLoad) { this.seen.add(t.name); this.colliders.add(meta.colliders); } // before the props: parked cars inside footprints / outside the fence are dropped below
    if (meta.cars?.length) meta.cars = meta.cars.filter((r) => this.inPlay(r[0], r[1]) && !this.colliders.insideBuilding(r[0], r[1]));
    const wmeta = (meta as unknown as { water?: WaterMeta }).water; // water: own shader, no shadows
    g.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      if ((o.material as THREE.Material).name === 'water') { if (wmeta) { o.material = waterMaterial(wmeta, this.shadows); (this.waters.get(t.name) ?? this.waters.set(t.name, []).get(t.name)!).push(o); } else o.visible = false; o.matrixAutoUpdate = false; o.updateMatrix(); return; }
      o.material = this.mat;
      o.receiveShadow = this.shadows;
      o.castShadow = this.shadows && o.name === 'buildings';
      o.matrixAutoUpdate = false;
      o.updateMatrix();
    });
    // small objects live in their own group so far tiles can skip them
    const props = new THREE.Group(), near = new THREE.Group(), far = new THREE.Group();
    const put = (grp: THREE.Object3D, label: string, list: (THREE.Object3D | undefined | null)[]) => {
      if (list.some((o) => !o)) console.warn('empty object from', label);
      const ok = list.filter((o): o is THREE.Object3D => !!o);
      for (const o of ok) if (!o.name) o.name = label;
      if (ok.length) grp.add(...ok);
    };
    treeField.add(t.name, meta.trees ?? []);   // all trees live in one distance-bucketed field (LOD0/1/impostor)
    const bikes = this.bikes?.build(meta.bikes ?? []) ?? [];
    put(props, 'props', buildProps(meta, this.shadows)); put(props, 'posters', buildPosters(meta.posters ?? [])); put(props, 'wild', buildWildPosters(meta.wild ?? []));
    put(props, 'graffiti', buildGraffiti((meta as unknown as { graffiti?: number[][] }).graffiti ?? []));
    put(near, 'bikes', bikes); // detailed bikes only close by (triangle budget)
    g.add(near, far);
    const m2 = meta as unknown as { housenumbers?: (number | string)[][]; streetsigns?: (number | string)[][]; decals?: number[][] };
    put(g, 'decals', buildDecals(m2.decals ?? [])); // flat on the road: always drawn with the tile
    const m3 = meta as unknown as { trafficsigns?: never[]; signals?: never[] };
    put(props, 'trafficsigns', buildTrafficSigns(m3.trafficsigns ?? []));
    put(props, 'signals', buildSignals(m3.signals ?? []));
    const m4x = meta as unknown as { construction?: number[][]; scooters?: number[][] };
    put(props, 'construction', buildConstruction(m4x.construction ?? []));
    const m5 = meta as unknown as { sites?: number[][]; cranes?: number[][]; workers?: number[][] };
    put(props, 'sites', buildSites(m5.sites ?? []));
    put(g, 'cranes', buildCranes(m5.cranes ?? [])); // cranes stay visible from afar
    const br = (meta as unknown as { bridges?: BridgeRows }).bridges;
    put(g, 'bridges', buildBridges(br));
    this.bridges.add(br, t.name);
    const solids: number[][] = []; // small solid obstacles for the player: [x, y, radius]
    for (const r of meta.trees ?? []) solids.push([r[0], r[1], Math.max(0.2, Math.min(0.5, (r[6] ?? 0.3) * 0.9))]);
    // lamps are cable lamps hanging 7.6 m above the carriageway (props.ts T.lamp): no ground collider (it was a phantom pole mid-road, ~99 % of them on the road mask)
    for (const r of meta.masts ?? []) solids.push([r[0], r[1], 0.2]);
    // bins are knockable (registered through attachKnocks, world/knockable.ts)
    for (const r of meta.benches ?? []) solids.push([r[0], r[1], 0.55]);
    this.colliders.addCircles(t.name, solids);
    attachKnocks(t.name, props, this.colliders);
    put(props, 'places', buildPlaces((meta as unknown as { places?: PlaceMeta }).places, this.shadows));
    put(props, 'details', buildDetails((meta as unknown as { details?: DetailMeta }).details, this.shadows)); // OSM street details (world/details.ts)
    put(props, 'yards', buildYards((meta as unknown as { yards?: YardMeta }).yards, this.shadows)); // courtyards, front gardens, shrubs (world/yards.ts)
    put(props, 'playground', buildPlaygrounds((meta as unknown as { playground?: PlaygroundRow[] }).playground ?? []));
    put(g, 'landmarks', buildLandmarks((meta as unknown as { landmarks?: LandmarkRow[] }).landmarks ?? [])); // landmark signs stay visible from afar
    put(g, 'fence', buildFence((meta as unknown as { fence?: number[][][] }).fence ?? [])); // always visible: it closes the map
    put(props, 'scooters', buildScooters(m4x.scooters ?? []));
    put(props, 'aframes', buildAFrames(meta.signs as never));
    put(props, 'sacks', buildSacks(m2.housenumbers ?? []));
    put(props, 'doors', buildDoors(m2.housenumbers ?? [])); put(props, 'numbers', buildHouseNumbers((m2.housenumbers ?? []) as never)); put(props, 'streetsigns', buildStreetSigns((m2.streetsigns ?? []) as never));
    const signs = buildSigns(meta.signs);
    if (signs) props.add(signs);
    g.add(props);
    const s = this.world.tile;
    const lods: THREE.Object3D[] = [];
    for (const grp of [props, near]) grp.traverse((o) => { if (o.userData.lo) lods.push(o); });
    const roofs = buildRooftops((meta as unknown as { roofs?: RoofRow[] }).roofs, this.shadows);
    for (const c of roofs) g.add(c.g);
    this.props.set(t.name, { g: props, near, far, bikes, lods, roofs, x: (t.ix + 0.5) * s, y: (t.iy + 0.5) * s });
    const hm = (meta as unknown as { hmap?: HeightData }).hmap;
    if (hm) this.hmaps.set(t.name, new Heights(hm));
    if (firstLoad) {
      this.masks.set(t.name, { m: meta.mask, bytes: Uint8Array.from(atob(meta.mask.bits), (c) => c.charCodeAt(0)) });
      this.onPaths(meta.paths);
      this.onLawn((meta as unknown as { lawn?: number[][] }).lawn ?? []);
      this.onFountains(meta.fountains ?? []);
      this.onSchools((meta as unknown as { schools?: number[][] }).schools ?? []);
      this.onSpots({ ...meta, benches: [...(meta.benches ?? []), ...((meta as unknown as { places?: { seats?: number[][] } }).places?.seats ?? [])] } as never); // benches, fountains, signs, workers -> standing/sitting people
    }
    this.scene.add(g);
    this.loaded.set(t.name, g);
  }
}
