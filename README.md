# SANDBOX ZÜRICH

Ein Open-World-Spiel im Browser in einem möglichst originalgetreuen Zürich (Kreise 4 und 5 sowie Teile von 3 und 9), spielbar auf Handy und PC. Work in progress.

**Spielen:** https://sandboxzurich.sandboxzurich-web.workers.dev

## Fehler melden
Fehler und Ideen werden als [GitHub Issues](https://github.com/dgnaegi/sandboxzurich/issues) gesammelt. Am einfachsten direkt im Spiel: Menü (☰ oder Esc) → **Fehler melden**, kurz beschreiben, **Absenden**. Ein GitHub-Konto brauchst du nicht: Das Spiel schickt den Bericht an eine kleine Worker-Route (`web/worker/`), die mit dem Token des Maintainers das Issue anlegt. Ort (inkl. Sprunglink `?at=…`), Fahrzeug, Gerät, Grafikstufe und Build hängt das Spiel automatisch an; du siehst vorher, was mitgeht, und nichts wird ohne Klick gesendet. Mit GitHub-Konto kannst du den Bericht auch selbst als vorausgefülltes Issue einreichen (Link auf derselben Seite). Einrichtung des Tokens: `docs/DEPLOY.md`, Abschnitt «Fehler melden».

## Credits
- Kartendaten © OpenStreetMap-Mitwirkende (ODbL)
- © swisstopo: swissBUILDINGS3D, swissALTI3D, swissSURFACE3D, SWISSIMAGE
- Stadt Zürich Open Data (CC0): Baumkataster, Beleuchtung ewz, Parkplätze, Sitzbänke, Brunnen, Abfallgefässe, Zweiradparkierung, Hydranten, Baustellen, Strassennamen, Widmungstafeln, Gastwirtschaftsbetriebe, Velonetz
- Kanton Zürich: Amtliche Vermessung (Bodenbedeckung)
- BFS: Eidg. Gebäude- und Wohnungsregister (GWR)
- Figuren: MakeHuman / MPFB (CC0)
- Bewegungen: CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu)
- Referenzfotos (nur als Vorlage, nicht im Spiel): Mapillary, Panoramax, Wikimedia Commons (CC BY-SA, Liste in `research/`)
- Musik (CC BY, via Wikimedia Commons, gekürzt): Jason Shaw / audionautix.com («Hip Hop 1 No Vocal», «Pool», CC BY 3.0), Nfaom loor («Boom bap instrumental», CC BY 4.0), Antti Luode («Hip Hop In B Minor», «Hop Hip Beat», CC BY 3.0); Details in `research/music.md`
- Schriften: Anton, Barlow, Archivo, Bebas Neue, DM Serif Display, Oswald, Space Mono, Permanent Marker (SIL OFL)
- Bibliotheken: three.js, meshoptimizer/gltfpack (MIT), n8ao
- Code: WTFPL
