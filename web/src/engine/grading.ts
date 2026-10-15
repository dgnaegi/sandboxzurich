import * as THREE from 'three';

/** Vector4 whose clone() returns itself, so ShaderLib's per-material uniform cloning shares ONE instance. */
class SharedVec4 extends THREE.Vector4 { clone(): this { return this; } }

/** Grade uniforms, shared by every material and the PC OutputPass. All zero = identity. */
export const gradeA = new SharedVec4();   // x = saturation-1, y = S-curve contrast, z = vignette, w = unused
export const gradeB = new SharedVec4();   // rgb = shadow tint (multiplicative offset)
export const gradeC = new SharedVec4();   // rgb = highlight tint
export const gradeD = new SharedVec4();   // xy = 1 / drawing-buffer size (vignette)

/** Bloom settings driven by daytime.ts, read by post.ts each frame (PC only). */
export const bloom = { strength: 0.3, threshold: 1.6, radius: 0.55 };

const GLSL = `
uniform vec4 gradeA; uniform vec4 gradeB; uniform vec4 gradeC; uniform vec4 gradeD;
vec3 CustomToneMapping( vec3 c ) {
	c = ACESFilmicToneMapping( c );
	float l = dot( c, vec3( 0.2126, 0.7152, 0.0722 ) );
	c = mix( vec3( l ), c, 1.0 + gradeA.x );                       // saturation
	c *= 1.0 + mix( gradeB.rgb, gradeC.rgb, smoothstep( 0.08, 0.7, l ) ); // split toning
	c = clamp( c, 0.0, 1.0 );
	c = mix( c, c * c * ( 3.0 - 2.0 * c ), gradeA.y );              // contrast S-curve
	vec2 uv = gl_FragCoord.xy * gradeD.xy - 0.5;
	c *= 1.0 - gradeA.z * smoothstep( 0.1, 0.5, dot( uv, uv ) );   // vignette
	return c;
}`;

/**
 * Colour grading as a custom tone mapper: no extra pass, no render target, so phones pay almost nothing.
 * Must run before the first material compiles. Also registers the shared uniforms on every built-in shader.
 */
export function installGrading(renderer: THREE.WebGLRenderer): void {
  const key = 'tonemapping_pars_fragment';
  const chunk = (THREE.ShaderChunk as Record<string, string>)[key];
  (THREE.ShaderChunk as Record<string, string>)[key] = chunk.replace('vec3 CustomToneMapping( vec3 color ) { return color; }', GLSL);
  for (const lib of Object.values(THREE.ShaderLib)) {
    const u = lib.uniforms as Record<string, { value: unknown }>;
    u.gradeA = { value: gradeA }; u.gradeB = { value: gradeB }; u.gradeC = { value: gradeC }; u.gradeD = { value: gradeD };
  }
  renderer.toneMapping = THREE.CustomToneMapping;
  setGradeResolution(renderer);
}

export function setGradeResolution(renderer: THREE.WebGLRenderer): void {
  const s = renderer.getDrawingBufferSize(new THREE.Vector2());
  gradeD.set(1 / Math.max(1, s.x), 1 / Math.max(1, s.y), 0, 0);
}

/** Uniform entries for hand-written ShaderMaterials that include tonemapping (sky, OutputPass). */
export const gradeUniforms = () => ({ gradeA: { value: gradeA }, gradeB: { value: gradeB }, gradeC: { value: gradeC }, gradeD: { value: gradeD } });
