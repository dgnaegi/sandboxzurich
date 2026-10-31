import * as THREE from 'three';

/** Cache busting: world data (tiles, models, textures, data JSON) is cached up to a day by the browser (public/_headers),
 *  so after a deploy old tiles could mix with a new landmarks.json. Every request for those paths gets ?v=<build>,
 *  which changes with each deploy (GITHUB_SHA at build time) and stays stable between deploys. Import first in main.ts. */
declare const __BUILD__: string;
/** Build id (12 chars of the commit SHA on CI, timestamp locally, 'dev' without Vite); also shown in bug reports. */
export const BUILD = typeof __BUILD__ === 'string' ? __BUILD__ : 'dev';
const VERSIONED = /^\/(tiles|data|models|tex|map)\//;

export function ver(url: string): string {
  if (!VERSIONED.test(url) || /[?&]v=/.test(url)) return url;
  return url + (url.includes('?') ? '&' : '?') + 'v=' + BUILD;
}

THREE.DefaultLoadingManager.setURLModifier(ver);
const nativeFetch = window.fetch.bind(window);
window.fetch = (input: RequestInfo | URL, init?: RequestInit) => nativeFetch(typeof input === 'string' ? ver(input) : input, init);
