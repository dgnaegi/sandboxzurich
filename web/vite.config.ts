import { defineConfig } from 'vite';

// __BUILD__ versions world-data URLs (src/engine/assetver.ts): commit SHA on CI, timestamp locally.
// VITE_WORLD_PROXY=https://<deployed site>: a checkout without locally built tiles/textures (they are not in git) serves the
// world data of that deployment through the dev server, so the client and the Playwright tests run against the live world.
// Tile metadata (tiles/*.json) is proxied only when it is missing locally: a mirrored or locally modified t_*.json wins, so
// deck rows and other JSON content can be iterated without rebuilding the GLB tiles.
import fs from 'node:fs';
import path from 'node:path';
const WORLD = process.env.VITE_WORLD_PROXY;
const localJson = (url: string) => /^\/tiles\/[^?]+\.json/.test(url) && fs.existsSync(path.join(__dirname, 'public', url.split('?')[0]));
const proxy = WORLD
  ? Object.fromEntries(['/tiles', '/tex', '/map', '/loading'].map((p) => [p, { target: WORLD, changeOrigin: true, bypass: (req: { url?: string }) => (req.url && localJson(req.url) ? req.url : undefined) }]))
  : undefined;

export default defineConfig({
  define: { __BUILD__: JSON.stringify((process.env.GITHUB_SHA ?? String(Date.now())).slice(0, 12)) },
  server: { proxy },
});
