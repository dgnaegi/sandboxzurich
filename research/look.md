# Look: Vice City in Zürich

- Grading = custom tone mapper (`web/src/engine/grading.ts`): ACES, saturation, split toning (cool shadows / warm highlights), S-curve contrast, vignette. Overrides `tonemapping_pars_fragment`; uniforms `gradeA..D` are shared via `ShaderLib` (SharedVec4.clone() returns itself), so no extra pass on phones. Sky includes `tonemapping_fragment`. All zero = identity.
- PC: N8AO -> UnrealBloomPass (half res, HDR threshold per time of day) -> OutputPass (same tone mapper).
- Parameters per keyframe in `daytime.ts` (`g`: sat, contrast, shadow tint, highlight tint, bloom strength, threshold).
- Palette: turquoise noon (zen 2a86d8 / hor a4e0e8), golden hour from 17:00, pink 18:36, violet 19:24, night deep blue-violet (0e0f3e / 3a2a78).
- Softer shadows: shadow.radius 4, intensity max 0.85. Fog starts at 90 m.
- Open: second tuning pass (night lifted: hemi 1.35, exposure 1.45, less contrast/magenta) not yet visually checked, tiles were being rebuilt.
