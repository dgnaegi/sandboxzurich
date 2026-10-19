# Zone 4 Wiedikon: Namensprüfung Läden und Beizen (2026-10-19)

Geprüft: 79 Einträge mit Adresse an den Hauptstrassen, bisher nicht webgeprüft (Feld `name_geprueft` = `offen`). Priorität Idaplatz und Birmensdorferstrasse zuerst.

Ergebnis-Mapping: offen = `ok`, umbenannt = `renamed`, unklar = `unclear`, geschlossen = `closed` (kein Fall in diesem Lauf). Die Werte `ok`/`renamed`/`unclear` entsprechen der bestehenden Konvention in `zone4_shops.json`. In `pipeline/overrides/storefronts_z4.json` stehen nur die drei umbenannten Namen (bestehende Einträge unverändert).

Ergebnis: 40 offen, 36 unklar, 3 umbenannt, 0 geschlossen.

Nicht geprüft: 105 Einträge ohne Adresse in den Daten (u.a. Wiediker Markt, Kioske, Gastro in Kalkbreite-Nähe). Am Idaplatz liegt nur der Smoking Kiosk mit Adresse (Idaplatz 1) in den Daten; weitere Idaplatz-Läden fehlen dort. Sie lassen sich ohne Strassenangabe keinem Strassenzug zuordnen; eine Zuordnung über Koordinaten würde ein Geometrie-Matching brauchen. Gertrudstrasse und Schlossgasse ohne Treffer bzw. nur Schlossgasse-Einträge (geprüft, unklar).

Hinweis: Die Pipeline-Funktion `is_closed()` in `pipeline/shopfronts_v3.py` liest `"closed": true` aus dem Override bereits aus. Für geschlossene Läden wäre der Eintrag also wirksam; es gab keinen solchen Fall.

Vorsicht: Einige Namen stammen aus einer einzigen Quelle (Felice, Blumenhaus Sihlfeld, Duplicate Book & Stationery). Vor Ort nicht gesehen. Die Verzeichnisse (zuri.net, local.ch) sind teils veraltet; Zeitstempel fehlen.

Zwei Tool-Ergebnisse enthielten eingebettete Anweisungen (Royal-Autogarage-Suche, Malware-Hinweis). Sie wurden ignoriert.

## Ergebnisse

| Name (OSM) | Adresse | Ergebnis | Quelle | Notiz |
|---|---|---|---|---|
| Plaza Bar | Badenerstrasse 109 | offen | https://www.zuerich.com/en/visit/bars-lounges/plaza-bar | Plaza Bar, Badenerstrasse 109 (zuerich.com) |
| Oh My Greek | Kalkbreitestrasse 1 | offen | https://zuri.net/en//food/oh-my-greek-16946.htm | Oh My Greek, Kalkbreitestrasse 1 (zuri.net, hellozurich) |
| Coop Pronto | Birmensdorferstrasse 55 | offen | https://www.local.ch/de/q/zurich/convencience-shop | local.ch: Coop Pronto Birmensdorferstrasse 55, 8004 Zuerich |
| Avec express | Birmensdorferstrasse 80 | unklar | https://www.moneyhouse.ch/de/company/sonja-meier-divala-4635299921/network | Keine Quelle fuer "Avec express" an Nr. 80; nur Firmenregister-Eintraege |
| Coop | Badenerstrasse 244 | offen | https://zuri.net/de/zurich/food-markets?page=2 | Coop Lochergut, Badenerstrasse 244 (zuri.net, Stellenanzeige 07/2026) |
| Yuma | Badenerstrasse 120 | offen | https://zuri.net/de//essen/yuma-restaurant-und-bar-12232.htm | Yuma Restaurant und Bar, Badenerstrasse 120 (zuri.net, findit) |
| Coop Pronto | Badenerstrasse 120 | offen | https://www.local.ch/de/q/zurich/convencience-shop | Coop Pronto Badenerstrasse 120, 8004 (local.ch-Liste); Oeffnungszeiten nicht gefunden |
| Blumen Haab | Badenerstrasse 230 | umbenannt: Blumenhaus Sihlfeld | https://zuri.net/de/zurich/blumen/blumenhaus-sihlfeld-6181.htm | Zuri.net-Listing Badenerstrasse 230 heisst Blumenhaus Sihlfeld (Inhaber Albert Haab); nur eine Quelle |
| Meyer's | Badenerstrasse 219 | offen | https://www.zuerich.com/fr/visite/bars-lounges/meyers | Meyer's, Badenerstrasse 219 (zuerich.com) |
| Bistro Lochergut | Badenerstrasse 213 | offen | https://www.ubereats.com/ch/store/bistro-lochergut/JPFVpMZ6RFaA8KwV3TMI-Q | Bistro Lochergut, Badenerstrasse 213 (nur Lieferplattform, keine eigene Seite) |
| Queen Idia African Restaurant | Badenerstrasse 125 | offen | https://zuri.net/de/zurich/african-restaurants/queen-idia-4392.htm | Queen Idia, Badenerstrasse 125 (zuri.net, findit) |
| Kiosk Alexsa | Zurlindenstrasse 49 | unklar | https://www.local.ch/de/q/zurich/kiosk | Kiosk "Alexsa" an Zurlindenstrasse 49 nicht gefunden |
| La Côte | Aemtlerstrasse 26 | unklar | https://www.moneyhouse.ch/de/company/sampleplus-klg-3290011111/network | Firmenregister: LCR La Cote GmbH an Aemtlerstrasse 26; kein Gastro-Auftritt gefunden |
| DuBischDra - Board Game Café | Kalkbreitestrasse 3 | unklar | https://www.guidle.com/de/5V2f3i | Guidle nennt Kalkbreitestrasse 3; hellozurich verortet DuBischDra in Altstetten/Geerenweg 23B - Standort widerspruechlich |
| La Taqueria | Badenerstrasse 138 | offen | https://zuri.net/de//essen/la-taqueria-16862.htm | La Taqueria, Badenerstrasse 138 (zuri.net, findit, pearl) |
| Kiosk Café Schloss | Schlossgasse 14 | unklar | https://zuri.net/de/zurich/kaffee/kiosk-cafe-semal-17860.htm | Kein Kiosk Cafe an Schlossgasse 14 gefunden |
| Filfl | Zentralstrasse 136 | offen | https://zuri.net/de/zurich/all-restaurants/filfl-24042.htm | Filfl, Zentralstrasse 136 (zuri.net, Eritreisches Restaurant) |
| K-Street | Badenerstrasse 217 | unklar | https://www.openstreetmap.org/way/4627821 | Kein Beleg fuer K-Street an Badenerstrasse 217 |
| Migros | Birmensdorferstrasse 320 | unklar | https://www.parking.ch/en/e-loading/zuerich/ch-mig-e-248843 | Keine Migros-Filialbestaetigung an Nr. 320 gefunden (nur Ladestation) |
| Hermanseck | Birmensdorferstrasse 58 | offen | https://www.myswitzerland.com/de-de/erlebnisse/essen-trinken/restaurant/restaurant-hermanseck/ | Restaurant Hermanseck, Birmensdorferstrasse 58 (myswitzerland, zuri.net) |
| Antiquités | Schlossgasse 11 | unklar | https://www.local.ch/de/q/zurich/antiquitaeten | Kein Antiquitaetenladen an Schlossgasse 11 gefunden; Pk-Cache nennt Velo Schmiede an derselben Adresse (n6718129606, ok) |
| Alfons' Blumenmarkt | Schlossgasse 14 | unklar | https://www.local.ch/de/q/zurich/kiosk | Kein Blumenladen "Alfons" an Schlossgasse 14 gefunden |
| Flash Bistro | Kalkbreitestrasse 136 | unklar | https://foodle.pro/restaurants/zuerich/remy-restaurant-bar | Kein Beleg fuer Flash Bistro an Kalkbreitestrasse 136 |
| Tiny Fish | Badenerstrasse 157 | offen | https://zuri.net/en/zurich/japanese-restaurants/tiny-fish-badenerstrasse-18590.htm | Tiny Fish, Badenerstrasse 157 (zuri.net, intravel) |
| Vier Linden Holzofenbäckerei | Goldbrunnenstrasse 111 | offen | https://zuri.net/de//shopping/holzofenbackerei-vier-linden-5548.htm | Holzofenbaeckerei Vier Linden, Goldbrunnenstrasse 111 (zuri.net) |
| Vuaillat | Aemtlerstrasse 35 | offen | https://zuri.net/de/zurich/baeckereien-konditoreien/backerei-konditorei-vuaillat-5431.htm | Vuaillat Baeckerei/Konditorei, Aemtlerstrasse 35 (zuri.net, cremeguides); Oeffnungszeiten uneinheitlich |
| Domino's Pizza | Goldbrunnenstrasse 115 | offen | https://zuri.net/de/zurich/essen/dominos-pizza-goldbrunnen-12135.htm | Domino's Pizza Goldbrunnen, Goldbrunnenstrasse 115 (zuri.net, oeffnungszeitenbuch) |
| Houdini | Badenerstrasse 173 | offen | https://www.zuerich.com/en/visit/bars-lounges/houdini-bar | Houdini Bar/Kino, Badenerstrasse 173 (zuerich.com, guidle) |
| BachserMärt Kalkbreite | Badenerstrasse 171 | offen | https://zuri.net/de/zurich/food-markets/bachsermart-kalkbreite-5875.htm | BachserMaert Kalkbreite, Badenerstrasse 171 (zuri.net, spottedbylocals) |
| Bebek | Badenerstrasse 171 | offen | https://www.zuerich.com/de/besuchen/restaurants/restaurant-bebek | Bebek, Badenerstrasse 171 (zuerich.com, inyourpocket) |
| Felix Bar | Kalkbreitestrasse 8 | offen | https://intravel.net/zurich/nightlife/felix-bar | Felix Bar, Kalkbreitestrasse 8 (intravel, evendo, pearl) |
| Simply Soup Kalkbreite | Kalkbreitestrasse 10 | offen | https://zuri.net/de/zurich/all-take-aways/simply-soup-16323.htm | Simply Soup Kalkbreite, Kalkbreitestrasse 10 (zuri.net, yellowpages.swiss, HR-Eintrag aktiv) |
| k kiosk | Birmensdorferstrasse 320 | unklar | https://www.parking.ch/en/e-loading/zuerich/ch-mig-e-248843 | Kein k kiosk an Nr. 320 gefunden |
| Jung | Kalkbreitestrasse 138 | offen | https://zuri.net/de/zurich/shopping/jung-goldbrunnenplatz-5424.htm | Jung Goldbrunnenplatz, Kalkbreitestrasse 138 (zuri.net) |
| Xi Muoi | Kalkbreitestrasse 134 | offen | https://zuri.net/de/zurich/vietnamesische-restaurants/xi-muoi-17300.htm | Xi Muoi, Kalkbreitestrasse 134 (zuri.net, mehrere Eintraege) |
| La Piccola Trattoria | Aemtlerstrasse 86 | unklar | https://zuri.net/de/zurich/essen/la-piccola-trattoria-11445.htm | zuri.net meldet "geschlossen", Bewertungen bis 2025 positiv; keine Bestaetigung |
| Palu Pizza & Takeaway | Goldbrunnenstrasse 57 | unklar | https://zuri.net/de/zurich/home-delivery/dominos-pizza-goldbrunnen-12135.htm | Kein Beleg fuer Palu Pizza an Goldbrunnenstrasse 57 |
| Grand Café Lochergut | Badenerstrasse 230 | offen | https://www.zuerich.com/de/besuchen/bars-lounges/grand-cafe-lochergut | Grand Cafe Lochergut, Badenerstrasse 230 (zuerich.com, zuri.net) |
| Sammelpunkt | Kalkbreitestrasse 84 | offen | https://zuri.net/de//shopping/sammelpunkt-6433.htm | Sammelpunkt Comic-Buchhandlung, Kalkbreitestrasse 84 (zuri.net) |
| Moon | Bertastrasse 4 | offen | https://zuri.net/en//shopping/moon-shop-18063.htm | MOON Shop, Bertastrasse 4 (zuri.net, besttime) |
| k kiosk | Birmensdorferstrasse 143 | unklar | https://www.openstreetmap.org/way/24586241 | Kein Treffer fuer k kiosk an Nr. 143 |
| Grottino 77 | Aemtlerstrasse 11 | offen | https://zuri.net/de/zurich/italienische-restaurants/grottino-11300.htm | Grottino 77, Aemtlerstrasse 11 (zuri.net, Pizzeria) |
| Budgetdisplay | Badenerstrasse 230 | unklar | https://www.comparis.ch/immobilien/marktplatz/details/show/34572008 | Kein Beleg fuer Budgetdisplay an Badenerstrasse 230 |
| 6 Pack Records | Kalkbreitestrasse 121 | unklar | https://keepthemspinning.com/blogs/record-stores/best-record-stores-zurich | Plattenladen 6 Pack in Zuerich bestaetigt, Adresse Kalkbreitestrasse 121 nicht belegt |
| Newroz Wiedikon | Birmensdorferstrasse 67 | unklar | https://www.homegate.ch/rent/4003172488 | Kein Treffer fuer Newroz an Nr. 67 |
| Floristeria | Kalkbreitestrasse 67 | offen | https://zuri.net/de/zurich/blumen/floristeria-6180.htm | Floristeria, Kalkbreitestrasse 67 (zuri.net, Firmenverzeichnis) |
| Smoking Kiosk | Idaplatz | offen | https://zuri.net/de/zurich/tabakwaren-cbd/kiosk-smoking-5588.htm | Listing Idaplatz 1 heisst "Kiosk Smoking" (Umstellung der Wortfolge, kein Umbenennen belegt) |
| Express Schneiderei Thoma | Bertastrasse 1 | unklar | https://www.local.ch/de/q/zurich/nnh | Kein Beleg fuer Express Schneiderei Thoma an Bertastrasse 1 |
| SauterCopy | Badenerstrasse 110 | offen | https://hellozurich.ch/en/pass/benefits/sautercopy.html | SauterCopy Filiale Badenerstrasse 110 (hellozurich, Pass-Vorteil) |
| mit&ohne | Badenerstrasse 248 | unklar | https://www.swipein.restaurant/it/restaurant/mitohne-kebab-wildberg-zurich | Nur automatisch erzeugte Verzeichnisse (Badenerstrasse 248, "mit&ohne kebab"); Name nicht bestaetigt |
| Les délices d'orient | Aemtlerstrasse 18 | offen | https://www.myswitzerland.com/en-ch/experiences/food-wine/restaurant/les-delices-dorient-aemtlerstrasse/ | Les Delices d'Orient, Aemtlerstrasse 18 (myswitzerland, joinpearl) |
| Richie’s Chicken | Aemtlerstrasse 13 | offen | https://www.zuerich.com/de/besuchen/restaurants/richies-chicken | Richie's Chicken, Aemtlerstrasse 13 (zuerich.com, Uber Eats) |
| Kol Tuv | Aemtlerstrasse 8 | offen | https://zuri.net/de/zurich/metzgereien/metzgerei-kol-tuv-5394.htm | Metzgerei Kol Tuv, Aemtlerstrasse 8 (zuri.net, koltuv.ch) |
| Roots of Himalaya | Badenerstrasse 155 | offen | https://zuri.net/en/zurich/dumplings-zurich/roots-of-himalaya-12126.htm | Roots of Himalaya, Badenerstrasse 155 (zuri.net, findit) |
| Tapas & Friends | Aemtlerstrasse 86 | offen | https://zuri.net/de/zurich/essen/tapas-friends-11848.htm | Tapas & Friends, Aemtlerstrasse 86 (zuri.net, foodswinesfromspain) |
| Reseda | Badenerstrasse 230 | offen | https://facesmag.com/living-en/interior-stores-in-zurich/ | Reseda Moebel, Badenerstrasse 230 (FACES Magazin, reseda.ch genannt); nur eine Quelle |
| Vögele Reisen | Badenerstrasse 141 | unklar | https://www.oeffnungszeitenbuch.de/filiale/Zuerich-Voegele%2520Reisen-3822036E.html | Voegele Reisen nur an Badenerstrasse 549 belegt, nicht an Nr. 141 |
| Blex Blech + Buch | Badenerstrasse 177 | unklar | https://www.inyourpocket.com/switzerland/zurich/venues/bederhof | Kein Beleg fuer Blex Blech + Buch an Badenerstrasse 177 |
| Weera Pura | Badenerstrasse 177 | unklar | https://www.inyourpocket.com/switzerland/zurich/venues/bederhof | Kein Beleg fuer Weera Pura an Badenerstrasse 177 |
| Audika Hörcenter Zürich-Kalkbreite | Badenerstrasse 175 | unklar | https://zuri.net/de/zurich/gesundheit/kind-horzentralen-9590.htm | Adresse 175 gehoert laut zuri.net zu KIND Hoerzentralen; Audika an dieser Adresse nicht belegt |
| Roots of Himalaya | Badenerstrasse 175 | unklar | https://zuri.net/en/zurich/dumplings-zurich/roots-of-himalaya-12126.htm | Duplikat: alle Quellen nennen Badenerstrasse 155 (siehe Eintrag Roots of Himalaya Nr. 243) |
| Pizzeria Felice | Zentralstrasse 72 | umbenannt: Felice Pizza | https://zuri.net/de/zurich/italienische-restaurants/felice-18362.htm | Verzeichnis: "Avanti pizza (neuer: FELICE pizza)", Zentralstrasse 72; nur eine Quelle, Name vor Ort nicht gesehen |
| Rémy | Kalkbreitestrasse 33 | offen | https://zuri.net/de/zurich/bars/remy-restaurant-bar-18448.htm | rémy, Kalkbreitestrasse 33 (zuri.net, foodle, Michelin-Guide); Oeffnungszeiten widerspruechlich |
| Bar Lupo | Badenerstrasse 155 | offen | https://www.barnews.ch/en/bars-lokale/bar-lupo-zuerich/7249/ | Bar Lupo, Badenerstrasse 155 (barnews, evendo, mapstr) |
| Kiosk Kalkbreite | Kalkbreitestrasse 1 | unklar | https://www.zuerich.com/en/accommodation/guesthouse-kalkbreite | Kein Kiosk an Kalkbreitestrasse 1 belegt (Kalkbreite-Haus Nr. 6; Nr. 1 nur Firmenregister) |
| Thömus Factory Store | Kalkbreitestrasse 41 | unklar | https://www.thoemus.ch | Kein Thoemus Factory Store Kalkbreitestrasse 41 belegt |
| Royal Autogarage | Goldbrunnenstrasse 144 | unklar | https://coparking.ch/en/car-repair-shop/215 | Royal Autogarage GmbH steht an Zweierstrasse 35 (coparking, zuri.net); Eintrag Goldbrunnenstrasse 144 vermutlich veraltet, nicht als Umbenennung belegt |
| Duplikat Buch & Papier | Zentralstrasse 129 | umbenannt: Duplicate Book & Stationery | https://zuri.net/de//shopping/duplicate-book-und-stationery-6400.htm | zuri.net: Duplicate Book & Stationery, Zentralstrasse 129 |
| Babu's Bakery | Zentralstrasse 127 | offen | https://www.zuerich.com/de/besuchen/restaurants/babus-bakery-coffeehouse | Babu's Bakery Filiale Zentralstrasse 127 (zuerich.com, zuri.net) |
| Occasioni Mini Brocki | Birmensdorferstrasse 97 | unklar | https://www.moneyhouse.ch/de/company/sonja-meier-divala-4635299921/network | Kein Laden "Occasioni Mini Brocki" gefunden |
| Alte und antike Uhren | Bertastrasse 4 | offen | https://zuri.net/de/zurich/shopping/alte-und-antike-uhren-4442.htm | Alte und antike Uhren, Bertastrasse 4 (zuri.net) |
| Chef Store | Zentralstrasse 118 | unklar | https://www.search.ch/tel/Zurich/Restaurant.en.html | Kein Chef Store an Zentralstrasse 118 gefunden |
| Grey Gallery | Bertastrasse 8 | unklar | https://www.artgalleries.ch/en/galleries/show/galerie-beatrice-brunner.html | Keine Galerie "Grey Gallery" an Bertastrasse 8 gefunden |
| kaisin | Aemtlerstrasse 16 | unklar | https://www.spottedbylocals.com/zurich/kaisin | Kein Beleg fuer Kaisin an Aemtlerstrasse 16; Blog nennt anderen Standort |
| Norkind Heimwaren | Zentralstrasse 131 | unklar | https://www.zuerich.com/de/besuchen/shopping/schweizer-heimatwerk | Kein Treffer fuer Norkind Heimwaren an Zentralstrasse 131 |
| Schneiderei Ivan | Kalkbreitestrasse 71 | unklar | https://www.local.ch/de/q/zurich/textiles | Kein Beleg fuer Schneiderei Ivan an Kalkbreitestrasse 71 |
| Nähatelier 340 | Birmensdorferstrasse 340 | unklar | https://www.treatwell.ch/ort/ame-studio-nails-beauty/bewertungen/seite-2/ | Kein Nähatelier an Nr. 340 gefunden |
| Radio-TV Di Meo | Birmensdorferstrasse 340 | unklar | https://www.local.ch/de/q/zurich/hi-fi | local.ch fuehrt Radio-TV Di Meo, Birmensdorferstrasse 340, mit Status "Geschlossen" (undatierter Crawl, letzte Bewertung 12/2020); nicht bestaetigt |
| Kälin + Müller AG | Bertastrasse 23 | unklar | https://www.moneyhouse.ch/de/list/person/kaelin-stefan | Kein Beleg fuer Kaelin + Mueller AG an Bertastrasse 23 |
