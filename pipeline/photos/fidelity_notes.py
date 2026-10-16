"""Adds facade notes read from fidelity photo pairs (research/fidelity.md) to research/buildings/visual_notes_v3.json.
Only adds addresses that have no v3 note yet; prints conflicts. Source = Panoramax pic id of the photo."""
import json, re, sys
F = 'research/buildings/visual_notes_v3.json'
cand = {c['id']: c for c in json.load(open('research/fidelity_cand.json'))}
def pid(i): return 'panoramax:' + re.search(r'pic=([0-9a-f-]+)', cand[i]['url']).group(1)
def N(hexc, mat='putz', fenster='hoch', laeden='keine', stil='gruenderzeit', g=None, det=(), note=''):
    return dict(hex=hexc, material=mat, fenster=fenster, laeden=laeden, rahmen='weiss', stil=stil, geschosse=g, details=list(det), notiz=note)
G, S = 'gruen', 'grau'
E = [  # (photo, [addresses], note)
 (42, ['Agnesstrasse 11', 'Agnesstrasse 13', 'Agnesstrasse 15', 'Agnesstrasse 19'], N('#e4e4df', laeden=G, stil='genossenschaft', g=5, note='hellgrau-weiss, dunkelgruene Fensterlaeden')),
 (42, ['Agnesstrasse 16', 'Agnesstrasse 18', 'Agnesstrasse 22'], N('#e6e3dc', stil='50er', g=5, det=['balkon'], note='weiss, vorgehaengte Balkone')),
 (54, ['Erismannstrasse 44', 'Erismannstrasse 46', 'Kanzleistrasse 203'], N('#b9714f', laeden='keine', g=5, note='terrakotta-braun, rote Storen im EG')),
 (57, ['Zypressenstrasse 144'], N('#93a8c6', laeden='braun', stil='genossenschaft', g=4, note='hellblau, braune Fensterlaeden')),
 (57, ['Zypressenstrasse 138', 'Zypressenstrasse 140', 'Zypressenstrasse 142'], N('#ebd7ad', stil='jugendstil', g=5, det=['balkon', 'erker'], note='creme-gelb, Balkone, Turmerker')),
 (57, ['Zypressenstrasse 126', 'Ernastrasse 17'], N('#ece9e2', laeden='braun', stil='genossenschaft', g=4, note='weiss, dunkle Fensterlaeden, Walmdach')),
 (70, ['Pflanzschulstrasse 49', 'Pflanzschulstrasse 47', 'Pflanzschulstrasse 36'], N('#86b4da', stil='50er', g=5, det=['balkon'], note='hellblau mit Balkonen')),
 (72, ['Kanzleistrasse 136', 'Herman-Greulich-Strasse 48', 'Anwandstrasse 79', 'Anwandstrasse 81'], N('#eceae5', stil='50er', g=5, det=['balkon'], note='weiss, Glasbalkone')),
 (72, ['Anwandstrasse 78', 'Anwandstrasse 82'], N('#e9e5da', stil='50er', g=5, det=['balkon'], note='weiss-creme, Balkone')),
 (86, ['Kernstrasse 8', 'Kernstrasse 10', 'Bauhallengasse 7', 'Bauhallengasse 11'], N('#e8b9b4', stil='gruenderzeit', g=5, det=['balkon', 'gesims'], note='rosa, Eckhaus')),
 (86, ['Wengistrasse 6', 'Wengistrasse 4', 'Wengistrasse 2a'], N('#d9cbb8', stil='gruenderzeit', g=5, det=['balkon'], note='graubeige')),
 (87, ['Schreinerstrasse 42', 'Schreinerstrasse 44', 'Kanzleistrasse 95'], N('#e2c97c', stil='gruenderzeit', g=5, det=['balkon', 'rustika'], note='ocker-gelb, grauer Rustika-Sockel')),
 (87, ['Kanzleistrasse 96', 'Kanzleistrasse 98', 'Schreinerstrasse 50', 'Schreinerstrasse 51'], N('#ebe9e4', stil='50er', g=5, det=['balkon'], note='weiss mit Balkonen')),
 (89, ['Feldstrasse 121', 'Feldstrasse 119'], N('#b8cce2', laeden=S, g=5, det=['balkon'], note='hellblau, graue Fensterlaeden')),
 (89, ['Feldstrasse 115', 'Brauerstrasse 98'], N('#e3c27a', laeden=S, g=5, det=['balkon'], note='ocker-gelb, graue Laeden')),
 (89, ['Brauerstrasse 97', 'Feldstrasse 111'], N('#cdbda6', mat='sandstein', laeden=S, g=5, det=['rustika'], note='graubeige, Sandstein-Sockel')),
 (96, ['Schimmelstrasse 9', 'Schimmelstrasse 11'], N('#e8e0b2', stil='50er', g=5, det=['balkon'], note='hellgelb/creme')),
 (98, ['Gartenhofstrasse 21', 'Gartenhofstrasse 19'], N('#e8dc7c', stil='gruenderzeit', g=5, det=['balkon'], note='gelb, Eckhaus mit Dachaufbau')),
 (99, ['Kanzleistrasse 97', 'Ankerstrasse 61', 'Ankerstrasse 63'], N('#cdb29f', fenster='band', laeden='keine', stil='50er', g=6, note='rosabeige Buerobau, Fensterbaender')),
 (101, ['Hohlstrasse 49', 'Marmorgasse 8', 'Marmorgasse 9', 'Langstrasse 63'], N('#ecd8d6', laeden='rot', stil='gruenderzeit', g=5, det=['gesims'], note='weiss-rosa, rote Laeden, Beizen im EG')),
 (101, ['Kernstrasse 52', 'Kernstrasse 56'], N('#b6d3b0', laeden=G, stil='gruenderzeit', g=5, det=['gesims'], note='mintgruen, gruene Laeden (Weinstube)')),
 (102, ['Rolandstrasse 27', 'Dienerstrasse 79', 'Dienerstrasse 83'], N('#dedad2', stil='gruenderzeit', g=5, det=['rustika'], note='gebrochen weiss, Rustika-Sockel')),
 (102, ['Nietengasse 9', 'Nietengasse 11', 'Magnusstrasse 14'], N('#a9d6d0', stil='gruenderzeit', g=5, note='tuerkis-mint')),
 (102, ['Nietengasse 16', 'Nietengasse 17', 'Magnusstrasse 22', 'Magnusstrasse 24'], N('#8fc4a2', stil='gruenderzeit', g=5, note='gruen')),
 (104, ['Neutrankengasse 25', 'Schöneggstrasse 28', 'Schöneggstrasse 30'], N('#e1b46c', stil='gruenderzeit', laeden='keine', g=5, det=['gesims'], note='ocker-orange, Ladenfenster im EG')),
 (104, ['Schöneggstrasse 34', 'Neutrankengasse 26'], N('#8fa1b6', stil='gruenderzeit', g=5, det=['gesims'], note='graublau')),
 (104, ['Schöneggstrasse 29', 'Sihlhallenstrasse 30'], N('#d8d1c1', laeden=G, stil='gruenderzeit', g=5, note='hellgrau-beige, dunkelgruene Laeden')),
 (108, ['Ottostrasse 6', 'Ottostrasse 8'], N('#e8b9ae', laeden=S, stil='genossenschaft', g=4, note='rosa, graue Laeden')),
 (108, ['Ottostrasse 5', 'Ottostrasse 7'], N('#e4d7a9', stil='gruenderzeit', g=5, det=['balkon'], note='cremegelb, Balkone')),
 (114, ['Werdstrasse 56', 'Werdstrasse 60', 'Birmensdorferstrasse 5', 'Birmensdorferstrasse 9'], N('#cbcbc7', stil='60er', fenster='band', g=6, det=['balkon'], note='hellgrau, Balkonbaender 60er')),
 (115, ['Stauffacherstrasse 31', 'Stauffacherstrasse 33', 'Stauffacherstrasse 35'], N('#d9ccb4', mat='sandstein', stil='gruenderzeit', laeden='keine', g=6, det=['balkon', 'erker', 'gesims'], note='sandsteinbeige, Eckhaus mit Balkonen, Laeden im EG')),
 (116, ['Stauffacherstrasse 54'], N('#e8dec6', stil='gruenderzeit', g=5, det=['balkon'], note='creme')),
 (116, ['Rotwandstrasse 37', 'Rotwandstrasse 39', 'Stauffacherstrasse 56'], N('#c0b9a9', mat='sandstein', stil='historismus', g=5, det=['rustika'], note='grauer Sandstein mit Rustika, rotbraune Fensterrahmen')),
]
d = json.load(open(F)); add = 0; skip = []
for ph, addrs, n in E:
    for a in addrs:
        if a in d: skip.append((a, d[a].get('hex'), n['hex'])); continue
        v = dict(n); v['quelle'] = pid(ph); d[a] = v; add += 1
json.dump(d, open(F, 'w'), ensure_ascii=False, indent=1)
print('added', add, 'skipped(existing)', len(skip))
for s in skip: print(' ', s)
