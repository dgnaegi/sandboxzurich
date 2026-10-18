# Movement round 2 (all changes marked `move2`)

Walking (`player/player.ts`): softer acceleration (7/11), sharp turns cost speed (cos factor, min 0.35), 0.25 m substeps (no tunnelling or jerks on frame spikes), glide round poles/signs when walking straight into them (tangent, side of the existing lean). Circle collider resolve (`collision.ts`) runs 2 passes with an early-out.
Bike: glancing hits slide (loss ~0.4 % per frame plus a share of the normal speed) and steer away slightly; fall only for a real head-on hit (speed into obstacle > 4.5 m/s and speed > 5.5).
Car (`drive.ts`): poles, signs and trunks (circle colliders) now bounce the car through the existing crash code; before they were passable.
Pedestrians (`pedestrians.ts`, hook set in `main.ts`): pushed out of circle colliders each frame (slide round poles). NPC traffic unchanged.
Rails: the player was never blocked by `railzone` (only spawn points and NPC paths/spots use it), so nothing to open up; #41 unchanged.

Measurements (tests/move_quality.mjs, 3 routes around Langstrasse, 30 poles walked head-on, 0.1 m off-centre, 4 s):
- stuck at poles before: 30/30 (y stayed at the pole); after: 0/30.
- perf.mjs phone 4x: avg 57 fps, 59 fps, 256 calls (no regression).
- gameplay/drive/crash/touch: drive, touch OK; crash passes (one flaky "HP bar visible" on the first run); gameplay "rode >4 m" FAILS at ?at=785,-635: the bike hits a solid at (787.3, -604.1) after 1.5 s. Not caused by these changes (same collision, milder losses); likely a new solid from concurrent landmark/bridge work. To check.
Not done: speed-dependent car steering/camera (already speed-limited in drive.ts), NPC traffic round signs, bike/car stuck routes (only walking measured).

## Part 2 (move2)
- NPC cars and bikes (`traffic.ts`, `Colliders.circleAhead`, hook in `main.ts`): brake before posts/signs/bollards in their lane (checked every 5th frame per agent); after 3 s of waiting they drive on, so no permanent jam.
- Player car: contact with thin posts is soft (restitution 0.5, half the crash strength) instead of a dead stop; walls/cars unchanged.
- Bike: thin posts are glided round (small speed loss, steering away); walls keep the old behaviour; fall only for real head-on hits.
- Measured (move_quality.mjs): car braking 30 km/h 3.3 m, 50 km/h 9.1 m (roughly 1 g, a little strong; left as is); bike 25 km/h 3.3 m; bike head-on at 10 poles: stuck 0, 8 falls (speed above 5.5 m/s head-on); rail bed (railzone, 10 m/s): p90 of |2nd difference| z 0.0007 / pitch 0.0004 = smooth, no jitter from ballast or sleepers (the heightmap has no sleeper relief); the player was never blocked on rails.
- Not changed: driving camera (already smoothed, no jitter found), curb bumps (spring body is fine).
- Flaky: crash.mjs «touch: HP bar visible while driving» fails intermittently (UI timing, not movement). perf phone 4x: 56 fps, 257 calls.
