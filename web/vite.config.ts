import { defineConfig } from 'vite';

// __BUILD__ versions world-data URLs (src/engine/assetver.ts): commit SHA on CI, timestamp locally.
// VITE_WORLD_PROXY=https://<deployed site>: a checkout without locally built tiles/textures (they are not in git) serves the
// world data of that deployment through the dev server, so the client and the Playwright tests run against the live world.
const WORLD = process.env.VITE_WORLD_PROXY;
const proxy = WORLD ? Object.fromEntries(['/tiles', '/tex', '/map', '/loading'].map((p) => [p, { target: WORLD, changeOrigin: true }])) : undefined;

export default defineConfig({
  define: { __BUILD__: JSON.stringify((process.env.GITHUB_SHA ?? String(Date.now())).slice(0, 12)) },
  server: { proxy },
});
