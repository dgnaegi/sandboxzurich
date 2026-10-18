import { defineConfig } from 'vite';

// __BUILD__ versions world-data URLs (src/engine/assetver.ts): commit SHA on CI, timestamp locally.
export default defineConfig({
  define: { __BUILD__: JSON.stringify((process.env.GITHUB_SHA ?? String(Date.now())).slice(0, 12)) },
});
