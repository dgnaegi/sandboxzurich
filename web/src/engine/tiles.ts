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
import { buildDoors } from '../world/doors';
import { buildConstruction, buildCranes, buildFence, buildScooters, buildSites } from '../world/construction';
import { buildAFrames, buildSacks, sackGroups } from '../world/streetlife';
import { buildTrafficSigns, buildSignals } from '../world/trafficsigns';

interface TileRef { name: string; ix: number; iy: number }
export interface Place { name: string; sub: string; x: number; y: number; yaw: number }
export interface World { tile: number; area: number[]; polygon?: number[][]; tiles: TileRef[]; heights: HeightData; places?: Place[] }
interface Mask { x0: number; y0: number; n: number; res: number; depth: number; bits: string }
interface TileMeta extends PropMeta { colliders: number[][][]; signs: Sign[]; posters: number[][]; wild?: number[][]; paths: number[][][]; mask: Mask }

const BASE = (import.meta.env.VITE_TILE_BASE_URL as string | undefined) ?? '/tiles';
const LOAD_RADIUS = 450;
const UNLOAD_RADIUS = 650;

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
  private props = new Map<string, { g: THREE.Group; near: THREE.Group; far: THREE.Group; bikes: THREE.Object3D[]; lods: THREE.Object3D[]; x: number; y: number }>();
  bikes: Bikes | null = null;
  treeRadius = 170;
  bikeRadius = 150;
  private seen = new Set<string>(); // colliders/paths registered once per tile
  private hmaps = new Map<string, Heights>();
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
    return new Tiles(world, scene, shadows, mat);
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
  groundAt(x: number, y: number, z: number): number { return this.bridges.heightAt(x, y, z) ?? this.ground(x, y); }

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
      const hi = d < this.bikeRadius;          // detailed bikes/cars only in the nearest tiles, stand-ins beyond
      for (const b of p.lods) { b.visible = hi; (b.userData.lo as THREE.Object3D).visible = !hi; }
    }
  }

  /** Load tiles whose centre is within LOAD_RADIUS of local (x, y). Resolves when all are in. */
  async update(x: number, y: number): Promise<void> {
    const s = this.world.tile, jobs: Promise<void>[] = [];
    for (const t of this.world.tiles) {
      if (Math.hypot((t.ix + 0.5) * s - x, (t.iy + 0.5) * s - y) < LOAD_RADIUS && !this.loaded.has(t.name)) {
        this.loaded.set(t.name, null);
        jobs.push(this.loadTile(t));
      }
    }
    // free GPU memory of far tiles (important on phones); colliders and masks stay (small)
    for (const [name, g] of this.loaded) {
      const t = this.props.get(name);
      if (!g || !t || Math.hypot(t.x - x, t.y - y) < UNLOAD_RADIUS) continue;
      this.scene.remove(g);
      g.traverse((o) => {
        const m = o as THREE.Mesh;
        if (m.geometry) m.geometry.dispose();
        const mat = m.material as THREE.MeshLambertMaterial | undefined;
        if (mat && mat !== this.mat && mat.map && (mat.map as THREE.CanvasTexture).isCanvasTexture) { mat.map.dispose(); mat.dispose(); }
      });
      for (const b of t.bikes) this.bikes?.forget(b);
      g.traverse((o) => sackGroups.delete(o));
      this.loaded.delete(name);
      this.props.delete(name);
      this.bridges.remove(name);
      treeField.remove(name);
    }
    await Promise.all(jobs);
  }

  private async loadTile(t: TileRef) {
    const [gltf, meta] = await Promise.all([
      this.loader.loadAsync(`${BASE}/${t.name}.glb`),
      fetch(`${BASE}/${t.name}.json`).then((r) => r.json() as Promise<TileMeta>),
    ]);
    const g = gltf.scene;
    g.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
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
    put(props, 'places', buildPlaces((meta as unknown as { places?: PlaceMeta }).places, this.shadows));
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
    this.props.set(t.name, { g: props, near, far, bikes, lods, x: (t.ix + 0.5) * s, y: (t.iy + 0.5) * s });
    const hm = (meta as unknown as { hmap?: HeightData }).hmap;
    if (hm) this.hmaps.set(t.name, new Heights(hm));
    if (!this.seen.has(t.name)) {
      this.seen.add(t.name);
      this.colliders.add(meta.colliders);
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
