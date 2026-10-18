import './engine/assetver'; // must stay first: versions world-data URLs
import * as THREE from 'three';
import { createRenderer } from './engine/renderer';
import { createPost } from './engine/post';
import { Quality } from './engine/quality';
import { Daytime, startMinutes } from './engine/daytime';
import { Skyline } from './engine/skyline';
import { BlobShadows } from './world/blobshadow';
import { Tiles } from './engine/tiles';
import { initKeyboardMouse } from './input/keyboard';
import { initTouch } from './input/touch';
import { consumeUse, actions as sbxActionsHook } from './input/actions';
import { Player } from './player/player';
import { Pedestrians } from './world/pedestrians';
import { HumanLib } from './world/humans';
import { loadTrees } from './world/trees';
import { treeField } from './world/tree_field';
import { CAR_GEO, carMaterial, carPick, loadCars } from './world/cars';
import { Scenes } from './world/scenes';
import { Lawns } from './world/lawns';
import { setYardsMobile } from './world/yards';
import { loadRailZone } from './world/railzone';
import { Events } from './world/events';
import { GameClock, bindClockPanel } from './ui/clock';
import { Bikes, loadBikes } from './world/bikes';
import { loadFurniture } from './world/props';
import { updateSignals } from './world/trafficsigns';
import { setSignNight } from './world/signs';
import { updateSacks } from './world/streetlife';
import { Transit } from './world/transit';
import { Railways } from './world/railways';
import { Landmarks3D } from './world/landmarks3d';
import { Traffic } from './world/traffic';
import { GameState, bindHud } from './gameplay/state';
import { Police } from './gameplay/police';
import { Missions } from './gameplay/missions';
import { VeloInfra } from './gameplay/velo';
import { Anecdotes } from './gameplay/anecdotes';
import { buildStops } from './world/stops';
import { CityMap } from './ui/map';
import { Locator } from './ui/locator';
import { chatLine } from './ui/chatter';
import { Menu } from './ui/menu';
import { loading, hasWebGL2 } from './ui/loading';
import { initHelp } from './ui/help';
import { settings } from './ui/settings';
import { Audio } from './engine/audio';
import { CarUse } from './player/vehicle_use';
import { TrafficLights } from './world/trafficlights';
import { addCar } from './world/night_lights';
import { parkedCars } from './world/parkedcars';
import { findSpot } from './player/spawn';
import type { Obb } from './player/drive';

// Spawn: Helvetiaplatz (local metres). ?at=x,y,yaw overrides it, ?t=HH:MM sets the time (screenshot tests).
// quests: off (User designs them later); map-first phase: no police, no theft stars, no pop-up messages (User 2026-10-15)
const QUESTS = false;
const GAMEPLAY = false;
const SPAWN = { x: 760, y: -905, yaw: -0.3 };
const STATION = { x: 1100, y: -846 }; // "Formular-Büro" on the Kasernenareal (former police barracks)

async function main() {
  const $ = (id: string) => document.getElementById(id)!;
  const canvas = $('view') as HTMLCanvasElement;
  const mobile = matchMedia('(pointer: coarse)').matches;
  const params = new URLSearchParams(location.search);
  if (GAMEPLAY) document.body.classList.add('gameplay'); // wanted stars only shown with gameplay
  initHelp(mobile);
  const R = createRenderer(canvas, mobile);
  const { renderer, scene, camera, followSun } = R;
  const daytime = new Daytime(R);

  const L = (p: Promise<unknown>) => loading.track(p);
  const map = new CityMap();
  await Promise.all([L(loadRailZone()), L(loadTrees('/models/trees', mobile ? 1 : 2)), L(loadCars()), L(loadBikes()), L(loadFurniture())]);
  setYardsMobile(mobile); // YARDS
  treeField.init(renderer, mobile, !mobile);
  const [tiles, humans] = await Promise.all([
    loading.track(Tiles.load(scene, !mobile, Math.min(8, renderer.capabilities.getMaxAnisotropy()))),
    loading.track(HumanLib.load('/models/humans', 4, mobile ? 10 : 40)),
    L(map.load()),
    L(document.fonts.load('26px Anton')),
  ]);
  const ground = (x: number, y: number) => tiles.ground(x, y);
  const bikes = new Bikes(scene);
  tiles.bikes = bikes;
  tiles.treeRadius = mobile ? 110 : 170;
  tiles.bikeRadius = mobile ? 110 : 150;
  tiles.roofRadius = mobile ? 150 : 250;
  const crowd = new Pedestrians(humans, mobile ? 16 : 36, ground);
  tiles.onPaths = (p) => crowd.addPaths(p);
  crowd.solid = (x, y, r) => tiles.colliders.resolveCircles(x, y, r);   // move2
  tiles.onSchools = (r) => crowd.schools.push(...r);
  tiles.onSpots = (m) => crowd.addSpots(m);
  scene.add(crowd.group);
  const skyline = new Skyline(scene, mobile);
  skyline.load().catch(() => {});
  const lawns = new Lawns(humans, mobile ? 8 : 20);
  tiles.onLawn = (r) => lawns.add(r);
  const fountainEgg = { id: 'brunnen', title: 'Brunnenwasser', text: 'Über 1200 Brunnen, fast alle mit Trinkwasser. Prost, Zürich!' };
  const pendingFountains: number[][][] = [];
  tiles.onFountains = (r) => pendingFountains.push(r);
  scene.add(lawns.group);

  const state = new GameState();
  const saved = state.load();
  bindHud(state);
  const at = params.get('at')?.split(',').map(Number);
  const [sx, sy, syaw] = at && at.length >= 2 ? at : saved?.x ? [saved.x, saved.y!, 0] : [SPAWN.x, SPAWN.y, SPAWN.yaw];
  await L(tiles.update(sx, sy));
  const player = new Player(sx, sy, tiles, humans.instance(humans.player));
  player.teleport(sx, sy, syaw ?? 0);
  scene.add(player.mesh);

  const transit = new Transit(scene, ground);
  const landmarks3d = new Landmarks3D(scene);
  if (mobile) { landmarks3d.loadR = 420; landmarks3d.unloadR = 560; landmarks3d.maxTex = 512; }
  const rail = new Railways(scene, tiles.mat, mobile ? 0.62 : 1); // phone: tracks within ~260 m
  const WHITE = new THREE.Color(0xf4f4f2);
  const traffic = new Traffic(scene, ground, CAR_GEO, carMaterial, (k) => (k % 23 === 0 && CAR_GEO.police && GAMEPLAY ? { type: 'police', color: WHITE } : k % 13 === 0 && CAR_GEO.taxi ? { type: 'taxi', color: k % 2 ? WHITE : new THREE.Color(0x1a1c20) } : carPick(k)));
  traffic.solidAhead = (x, y, hx, hy, d, w) => tiles.colliders.circleAhead(x, y, hx, hy, d, w);   // move2: NPC cars/bikes stop for posts in their lane
  const trafficLights = new TrafficLights(scene);
  const scenes = new Scenes(humans, ground);
  // people waiting at tram/bus stops (groups of 3 next to the track, right-hand side)
  let stops: THREE.Group | null = null;
  void fetch('/data/transit.json').then((r) => r.json()).then((d) => {
    scene.add(stops = buildStops(d, ground));
    for (const l of d.lines) for (const st of l.stops) {
      let s = st.s;
      for (let i = 0; i + 1 < l.pts.length; i++) {
        const [ax, ay] = l.pts[i], [bx, by] = l.pts[i + 1], L = Math.hypot(bx - ax, by - ay);
        if (s > L) { s -= L; continue; }
        const t = s / L, x = ax + (bx - ax) * t, y = ay + (by - ay) * t, h = Math.atan2(bx - ax, by - ay);
        const px = x + Math.cos(h) * 3.2, py = y - Math.sin(h) * 3.2;
        if (!tiles.colliders.inside(px, py)) lawns.add([[px, py, ground(px, py), h - Math.PI / 2, 2]]);
        break;
      }
    }
  });
  const events = new Events(humans, ground, mobile);
  const velo = new VeloInfra();
  const anecdotes = new Anecdotes();
  const locator = new Locator();
  const npc = (await loading.track(fetch('/data/npc.json').then((r) => r.json()))) as { hourly: number[] };
  // passer-by density by hour (Statistik Stadt Zürich proxy) + Fri/Sat nightlife on the Langstrasse
  const density = (min: number, wd: number) => {
    const h = Math.floor(min / 60) % 24, f = npc.hourly[h] ?? 0.5;
    const night = (wd === 4 || wd === 5) && (h >= 21 || h <= 3) ? 0.85 : 0;
    return 0.3 + 0.7 * Math.max(f, night);
  };
  await Promise.all([landmarks3d.load(), rail.load(), transit.load(), transit.loadModels(), traffic.load(), scenes.load(), events.load(), velo.load(), anecdotes.load(), locator.load()].map(L));
  if (!params.has('exact')) { // never start in a building / landmark / on rail land, water or tram tracks (?exact keeps the raw ?at= for screenshot tests)
    const [fx, fy] = await findSpot({ tiles, landmarks: landmarks3d }, player.x, player.y);
    if (Math.hypot(fx - player.x, fy - player.y) > 0.01) player.teleport(fx, fy, player.yaw);
  }
  scene.add(events.group);
  traffic.maxCars = mobile ? 20 : 45;
  traffic.maxBikes = mobile ? 8 : 20;
  const blobs = new BlobShadows(scene, { crowd: crowd.group, cars: () => traffic.positions(), player: player.mesh, ground, sunDir: R.sunDir });
  scene.add(scenes.group);
  scenes.visRadius = crowd.visRadius = mobile ? 70 : 120;
  for (const r of pendingFountains) scenes.addEggPoints(fountainEgg, r);
  tiles.onFountains = (r) => scenes.addEggPoints(fountainEgg, r);
  const police = new Police(humans, tiles.colliders, ground);
  if (GAMEPLAY) scene.add(police.group);
  // quests/missions: all off (User 2026-10-15, designs them later); code stays, switch QUESTS to re-enable
  const missions = new Missions(state.missions, ground);
  if (QUESTS) scene.add(missions.group);

  // --- UI feedback --------------------------------------------------------------------------------------
  let toastTimer = 0, bigTimer = 0;
  const toast = (kicker: string, title: string, text: string) => {
    if (!GAMEPLAY) return;
    $('toast-kicker').textContent = kicker; $('toast-title').textContent = title; $('toast-text').textContent = text;
    $('toast').classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => $('toast').classList.remove('on'), 5000);
  };
  const bigText = (title: string, text: string, kind: string) => {
    const el = $('bigtext');
    el.className = kind; el.style.display = 'block';
    $('bigtext-title').textContent = title; $('bigtext-text').textContent = text;
    clearTimeout(bigTimer);
    bigTimer = window.setTimeout(() => { el.style.display = 'none'; }, kind === 'start' ? 6000 : 4500);
  };
  scenes.onFound = (egg, n, total) => toast(`EASTER EGG ${n}/${total}`, egg.title, egg.text);
  anecdotes.onShow = (a, n, total) => toast(a.kind === 'street' ? 'STRASSENNAME' : `ZÜRICH-WISSEN ${n}/${total}`, a.title, a.text);
  missions.onText = (t, x, k) => { bigText(t, x, k); if (k !== 'start') audio.jingle(k === 'pass'); };
  // events (market, Critical Mass, demo) happen without announcement toasts (User 2026-10-15)
  missions.onReward = (chf) => { state.addMoney(chf); state.save(player.x, player.y); };

  const jump = (x: number, y: number, yaw = player.yaw) => {
    void findSpot({ tiles, landmarks: landmarks3d }, x, y).then(([px, py]) => player.teleport(px, py, yaw));
  };
  map.onJump = (x, y) => { if (player.driving) carUse.exit(); player.dismount(); jump(x, y); };
  const audio = new Audio();
  transit.onBell = () => audio.tramBell(0.18);
  const menu = new Menu();
  menu.onMute = (m) => audio.setMuted(m);
  menu.onMap = () => map.toggle(true);
  // wanted stars attach here later (map phase: off): car theft is only 'seen' in traffic
  const onCarTheft = (kind: 'parked' | 'traffic') => {
    if (GAMEPLAY && kind === 'traffic') { state.wanted(state.stars + 1); toast('AUTODIEBSTAHL', '★ Gesehen!', 'Jemand hat dich beim Auto-Klauen beobachtet.'); }
  };
  // cars: take parked or passing cars (E), drive with WASD/stick; obstacles for the driven car = traffic, trams, trains
  const obb = (v: { x: number; y: number; heading: number; id?: number }, len: number, wid: number): Obb => ({ x: v.x, y: v.y, fx: Math.cos(v.heading), fy: Math.sin(v.heading), hl: len / 2, hw: wid / 2, id: v.id });
  const carUse = new CarUse(player, tiles, traffic, humans, audio, renderer, scene, () => [
    ...traffic.positions().map((v) => { const o = obb(v, v.kind === 'car' ? v.len : 1.8, v.kind === 'car' ? 1.8 : 0.6); if (v.kind !== 'car') o.id = undefined; return o; }),
    ...transit.colliders().map((v) => obb(v, v.len, v.width)), ...rail.colliders().map((v) => obb(v, v.len, v.width)),
  ], () => daytime.night);
  carUse.onTheft = onCarTheft;
  carUse.onHint = (text) => { // short hint line (no pop-up card)
    let el = document.getElementById('drivehint');
    if (!el) { el = document.createElement('div'); el.id = 'drivehint'; el.style.cssText = 'position:fixed;left:50%;top:18%;transform:translateX(-50%);padding:8px 14px;border-radius:10px;background:#000b;color:#fff;font:600 15px system-ui,sans-serif;z-index:30;pointer-events:none;transition:opacity .4s'; document.body.appendChild(el); }
    el.textContent = text; el.style.opacity = '1';
    window.setTimeout(() => { if (el) el.style.opacity = '0'; }, 4500);
  };
  player.onBikeCrash = () => { // hard impact on the bike: rider falls, bike stays behind
    const left = player.dismount();
    if (left) bikes.drop(left.x, left.y, left.z, left.h, left.color);
    audio.carCrash(0.35);
  };

  const post = !mobile && !params.has('nopost') ? createPost(renderer, scene, camera) : null;
  const quality = new Quality(renderer, mobile, !!post, scene.fog as THREE.Fog | null);
  audio.setMuted(settings.muted);
  audio.setMusic(settings.music, settings.musicVol);
  menu.onMusic = (on, vol) => audio.setMusic(on, vol);
  (window as unknown as { __music: () => unknown }).__music = () => audio.music?.state;
  renderer.info.autoReset = false;
  initKeyboardMouse(canvas);
  initTouch($('stick'), $('knob'));
  loading.finish();
  if (params.has('map')) map.toggle(true);
  if (params.has('debug')) document.body.classList.add('debug');

  // --- interaction: bikes -------------------------------------------------------------------------------
  // what E would do now: closest of bike and car
  const pickTarget = () => {
    const slot = bikes.nearest(player.x, player.y), car = carUse.nearest();
    if (car && (!slot || car.d < Math.hypot(slot.x - player.x, slot.y - player.y))) return { kind: 'car' as const, car, slot: null };
    return slot ? { kind: 'bike' as const, slot, car: null } : null;
  };
  const use = () => {
    if (player.driving) { carUse.requestExit(); return; }
    if (player.riding) {
      const left = player.dismount();
      if (left) bikes.drop(left.x, left.y, left.z, left.h, left.color);
      return;
    }
    const pick = pickTarget();
    if (pick?.kind === 'car') { void carUse.enter(pick.car); return; }
    const slot = pick?.slot;
    if (!slot) return;
    const own = slot.mesh === bikes.dropped;
    bikes.take(slot);
    player.mount(slot);
    audio.bikeBell();
    if (!own && GAMEPLAY) {
      const seen = police.nearest(player.x, player.y) < 35 || Math.random() < 0.25;
      if (seen) { state.wanted(state.stars + 1); toast('VELODIEBSTAHL', '★ Gesehen!', 'Jemand hat dich beim Velo-Klauen beobachtet.'); }
    }
  };

  const busted = () => {
    player.dismount();
    police.clear();
    const fine = Math.round(state.money * 0.1);
    state.addMoney(-fine);
    state.wanted(0);
    bigText('VERHAFTET', `Ab ins Formular-Büro: 47 Formulare in dreifacher Ausführung. Busse CHF ${fine}.`, 'fail');
    missions.end();
    jump(STATION.x, STATION.y);
  };

  // speech bubbles: passers-by greet now and then
  let honkT = 0, laneTipShown = false;
  let bubbleT = 4, bubbleObj: THREE.Object3D | null = null, bubbleLeft = 0;
  const bubble = $('bubble');
  const vproj = new THREE.Vector3();
  const updateBubble = (dt: number) => {
    bubbleT -= dt; bubbleLeft -= dt;
    if (bubbleT <= 0) {
      bubbleT = 6 + Math.random() * 8;
      const n = crowd.nearest(player.x, player.y);
      if (n && n.d < 5) {
        bubble.textContent = chatLine({ place: locator.square(player.x, player.y) ?? locator.street(player.x, player.y) ?? '', min: clk.min, day: clk.day, night: daytime.night > 0.5 });
        bubbleObj = n.obj; bubbleLeft = 2.5;
      }
    }
    if (bubbleObj && bubbleLeft > 0) {
      vproj.setFromMatrixPosition(bubbleObj.matrixWorld); vproj.y += 2.1; vproj.project(camera);
      bubble.style.display = vproj.z < 1 ? 'block' : 'none';
      bubble.style.left = `${(vproj.x * 0.5 + 0.5) * innerWidth}px`; bubble.style.top = `${(-vproj.y * 0.5 + 0.5) * innerHeight}px`;
    } else bubble.style.display = 'none';
  };

  // --- main loop ----------------------------------------------------------------------------------------
  // game calendar: 24 real minutes = 1 day; starts on a Friday unless ?day=0..6 (Mo..So)
  const clk = new GameClock(startMinutes(), Number(params.get('day') ?? 4) % 7, params.has('t') || params.has('day'));
  bindClockPanel(clk);
  (window as unknown as { sbxClock: GameClock }).sbxClock = clk;
  let transitMin = clk.min;
  const clock = new THREE.Clock();
  let frames = 0, acc = 0, lastStream = 0, lastStats = 0, lastSave = 0;
  renderer.setAnimationLoop(() => {
    const raw = clock.getDelta(), dt = Math.min(raw, 0.1);
    acc += dt;
    quality.tick(raw);
    renderer.info.reset();
    if (map.open) { map.drawBig(player.x, player.y, player.heading); return; }
    if (menu.open) return;
    clk.tick(dt);                         // 1 game minute per real second (x10 / x60 / paused via the clock panel)
    transitMin = (transitMin + dt / 60) % 1440; // vehicles run on real time
    if (consumeUse()) use();
    // cycling infrastructure: faster and shown on the radar while riding
    const lane = player.riding ? velo.at(player.x, player.y) : null;
    player.boost = lane ? 1.2 : 1;
    map.overlay = player.riding ? velo.lines.map((l) => l.p) : [];
    if (lane && !laneTipShown) { laneTipShown = true; toast('VELO-INFRASTRUKTUR', '+20 % Tempo', 'Auf Velowegen und Velostreifen kommst du schneller und sicherer voran.'); }
    player.update(dt, camera);
    crowd.max = Math.round(quality.peds * density(clk.min, clk.day));
    crowd.clock(clk.min, clk.day);
    // school run Mon–Fri: 07:30–08:15, 11:45–12:15, 15:30–16:30
    crowd.schoolRun = clk.day < 5 && ((clk.min >= 450 && clk.min < 495) || (clk.min >= 705 && clk.min < 735) || (clk.min >= 930 && clk.min < 990));
    crowd.update(dt, player.x, player.y, player.driving);
    scenes.min = clk.min;
    scenes.update(dt, player.x, player.y);
    anecdotes.update(dt, player.x, player.y);
    lawns.update(dt, player.x, player.y);
    updateBubble(dt);
    events.update(dt, clk.day, clk.min, player.x, player.y);
    // moving vehicles push the player aside (no damage, comic bump); blocked cars honk
    honkT -= dt;
    for (const v of traffic.positions()) {
      if (v.kind !== 'car') continue;
      if (honkT <= 0) {
        const fx = Math.cos(v.heading), fy = Math.sin(v.heading), rx = player.x - v.x, ry = player.y - v.y;
        const ahead = rx * fx + ry * fy, side = Math.abs(-rx * fy + ry * fx);
        if (ahead > 2 && ahead < 8 && side < 1.2) { audio.honk(); honkT = 3 + Math.random() * 3; }
      }
      const c = Math.cos(v.heading), s = Math.sin(v.heading);
      if (!player.driving) for (const o of [-1.3, 0, 1.3]) {
        const cx = v.x + c * o, cy = v.y + s * o, dx = player.x - cx, dy = player.y - cy, d = Math.hypot(dx, dy);
        if (d < 1.25 && d > 1e-3) { player.x = cx + (dx / d) * 1.25; player.y = cy + (dy / d) * 1.25; }
      }
    }
    if (!player.driving) for (const v of [...transit.colliders(), ...rail.colliders()]) {
      const c = Math.cos(v.heading), s = Math.sin(v.heading), dx = player.x - v.x, dy = player.y - v.y;
      const along = dx * c + dy * s, across = -dx * s + dy * c, hl = v.len / 2 + 0.3, hw = v.width / 2 + 0.35;
      if (Math.abs(along) < hl && Math.abs(across) < hw) {
        const push = (hw - Math.abs(across)) * Math.sign(across || 1);
        player.x += -s * push; player.y += c * push;
      }
    }
    transit.night = daytime.night;
    transit.update(dt, transitMin, player.x, player.y);
    rail.update(dt, transitMin, player.x, player.y);
    landmarks3d.update(player.x, player.y);
    carUse.update(dt);
    traffic.update(dt, player.x, player.y, player.driving ? player.driving.circlesWorld() : [{ x: player.x, y: player.y, r: 1.4 }]);
    trafficLights.update(traffic.positions(), acc, daytime.night, ground, player.x, player.y);
    if (player.driving && daytime.night > 0.3) { const hx = Math.sin(player.heading), hy = Math.cos(player.heading); addCar(player.x + hx * 2.2, ground(player.x, player.y) + 0.7, -(player.y + hy * 2.2), hx, -hy, Math.min(1, daytime.night)); }
    if (QUESTS) missions.update(dt, player.x, player.y, !!player.riding);
    if (GAMEPLAY && police.update(dt, player.x, player.y, state.stars)) { busted(); audio.jingle(false); }
    audio.update(dt, daytime.night, state.stars > 0, police.nearest(player.x, player.y), {
      x: player.x, y: player.y, heading: player.heading, night: daytime.night, density: density(clk.min, clk.day), hour: Math.floor(clk.min / 60) % 24,
      trams: transit.colliders(),
    });
    if ((frames & 63) === 0 && transit.colliders().some((v) => Math.hypot(v.x - player.x, v.y - player.y) < 25) && Math.random() < 0.3) audio.tramBell();
    state.tick(dt, police.nearest(player.x, player.y) < 50);
    updateSignals(acc);
    if ((frames & 15) === 0) { setSignNight(daytime.night); updateSacks(clk.day, clk.min); }
    daytime.set(clk.min);
    daytime.follow(player.mesh.position);
    followSun(player.mesh.position);
    skyline.update(camera.position);
    blobs?.update(!renderer.shadowMap.enabled, daytime.sunUp, camera.position);
    tiles.cull(player.x, player.y, quality.detailRadius);
    if (stops && (frames & 15) === 0) for (const o of stops.children) o.visible = Math.hypot(o.position.x - player.x, -o.position.z - player.y) < quality.detailRadius; // shelters: 5 calls each
    if (acc - lastStream > 1) { lastStream = acc; void tiles.update(player.x, player.y); }
    if (acc - lastSave > 10) { lastSave = acc; state.save(player.x, player.y); }
    if (post && quality.post) post.render(); else renderer.render(scene, camera);

    const blips = [...(QUESTS ? missions.blips() : []), ...(state.stars ? police.positions().map((p) => ({ ...p, color: frames % 20 < 10 ? '#3060ff' : '#ff3030' })) : [])];
    map.drawRadar(player.x, player.y, player.yaw, player.heading, blips);
    const tgt = player.driving || player.riding ? null : pickTarget();
    const prompt = player.driving ? (player.driving.dead ? (mobile ? 'Auto kaputt – E = aussteigen' : 'Auto kaputt – E zum Aussteigen') : Math.abs(player.speed) < 3 ? (mobile ? 'E = aussteigen' : 'E drücken: aussteigen') : '')
      : tgt?.kind === 'car' ? (mobile ? 'E = Auto nehmen' : 'E drücken: Auto nehmen')
      : tgt?.kind === 'bike' ? (mobile ? 'E = Velo nehmen' : 'E drücken: Velo nehmen') : player.riding && player.speed < 0.5 ? 'E = absteigen' : '';
    $('prompt').style.display = prompt ? 'block' : 'none';
    $('prompt').textContent = prompt;
    if (QUESTS) $('mission').textContent = missions.hud();
    if (++frames % 30 === 0) {
      const i = renderer.info.render, near = map.nearestPlace(player.x, player.y);
      const mem = (performance as unknown as { memory?: { usedJSHeapSize: number } }).memory?.usedJSHeapSize ?? 0;
      $('stats').textContent = `${Math.round(30 / (acc - lastStats))} fps · ${i.calls} calls · ${(i.triangles / 1000).toFixed(0)}k tris · q${quality.level} · ${(mem / 1e6) | 0} MB JS`;
      const nearPlace = near && Math.hypot(near.x - player.x, near.y - player.y) < 70 ? near.name : null;
      $('place-name').textContent = locator.square(player.x, player.y) ?? locator.street(player.x, player.y, 14) ?? nearPlace ?? locator.street(player.x, player.y) ?? near?.name ?? '';
      $('place-kreis').textContent = locator.kreis(player.x, player.y) ?? map.kreisAt(player.x, player.y);
      $('clock').textContent = clk.label();
      lastStats = acc;
    }
  });
  Object.assign(window, { sbxReady: true, sbxActions: sbxActionsHook, sbxFindSpot: (x: number, y: number) => findSpot({ tiles, landmarks: landmarks3d }, x, y), sbxPlayer: player, sbxScene: scene, sbxState: state, sbxBikes: bikes, sbxCarUse: carUse, sbxParked: parkedCars, sbxTraffic: traffic, sbxEvents: events, sbxTransit: transit, sbxRail: rail, sbxRenderer: renderer, sbxCamera: camera, sbxTiles: tiles, sbxDaytime: daytime, sbxMap: map, sbxCrowd: crowd }); // hooks for Playwright tests
}

if (!hasWebGL2()) loading.fail('Dein Browser unterstützt WebGL 2 nicht oder hat es abgeschaltet. Bitte aktualisiere den Browser (Chrome, Firefox, Safari ab iOS 15) oder aktiviere die Hardwarebeschleunigung.', false);
else {
  const fail = (e: unknown) => { console.error(e); loading.fail('Das Spiel konnte nicht geladen werden. Bitte prüfe die Verbindung und lade neu.'); };
  main().catch(fail);
  window.addEventListener('unhandledrejection', (e) => fail(e.reason));
}
