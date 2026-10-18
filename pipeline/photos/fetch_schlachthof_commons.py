"""Targeted Commons download (800 px thumbs) for Schlachthof Zuerich + Letzipark -> data/raw/photos/schlachthof/commons/, meta research/v3/photos_schlachthof_commons.json"""
import json, urllib.request, urllib.parse, re, time, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
TITLES = """Schlachthof Zürich 2011-08-16 15-53-18 ShiftN.jpg
Lokremise Schlachthof Zürich BAZ 007581.jpg
Schlachthof Zürich 1980 BAZ 025729.jpg
Schlachthof Zürich 2004 DMP 067525.jpg
Schlachthof Zürich BAZ 025847.jpg
Schlachthof Zürich 2011-08-16 15-50-30.JPG
Schlachthof Zürich 2011-08-16 15-47-38.jpg
Schlachthof Zürich 2011-08-16 15-47-22.jpg
Schlachthof Zürich 2011-08-16 15-52-22 ShiftN.jpg
Schlachthof Zürich 2011-08-16 15-49-58.jpg
Schlachthof Zürich, Westportal.jpg
Schlachthof in Zürich-Aussersihl.jpg
Einkaufszentrum Letzipark, Zurich, June 2024.jpg
Altstetten - Letzipark - Hohlstrasse 2013-12-01 16-52-15 (P7800).JPG
Altstetten - Letzipark - Hohlstrasse 2013-12-01 17-34-54 (P7800).JPG
Altstetten - Letzipark - Hohlstrasse 2013-12-01 16-54-10 (P7800).JPG
Baslerstrasse Richtung Letzipark - panoramio.jpg
Popeyes in Zurich, June 2024, Letzipark.jpg""".split("\n")
H = {'User-Agent': 'sandboxzurich-research/1.0 (contact via repo)'}
out = ROOT / "data/raw/photos/schlachthof/commons"; out.mkdir(parents=True, exist_ok=True)
mp = ROOT / "research/v3/photos_schlachthof_commons.json"
meta = json.load(open(mp)) if mp.exists() else {}


def get(u, tries=6):
    for k in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=H)).read()
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(15 * (k + 1))
    raise RuntimeError(u)


for t in TITLES:
    fn = re.sub(r'[^A-Za-z0-9.]+', '_', t)[:60]
    if not fn.lower().endswith('.jpg'): fn += '.jpg'
    if (out / fn).exists(): continue
    u = "https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=800&format=json&titles=" + urllib.parse.quote("File:" + t)
    ii = list(json.loads(get(u))['query']['pages'].values())[0].get('imageinfo', [{}])[0]
    if not ii.get('thumburl'): print('no', t); continue
    (out / fn).write_bytes(get(ii['thumburl'])); time.sleep(3)
    em = ii.get('extmetadata', {})
    meta[fn] = {'title': t, 'license': em.get('LicenseShortName', {}).get('value'), 'author': re.sub('<[^>]+>', '', em.get('Artist', {}).get('value', ''))[:60],
                'date': em.get('DateTimeOriginal', {}).get('value', '')[:30], 'desc': re.sub('<[^>]+>', '', em.get('ImageDescription', {}).get('value', ''))[:150]}
    json.dump(meta, open(mp, 'w'), indent=1, ensure_ascii=False)
    print(fn, meta[fn]['license'], meta[fn]['date'])
