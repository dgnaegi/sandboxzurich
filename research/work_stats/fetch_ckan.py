import json, sys, urllib.request, os
BASE = "https://data.stadt-zuerich.ch/api/3/action/package_show?id="
OUT = "/Users/danielgnagi/sandboxzurich/data/raw/stats"
pkgs = sys.argv[1:]
for p in pkgs:
    try:
        d = json.load(urllib.request.urlopen(BASE + p, timeout=60))["result"]
    except Exception as e:
        print("ERR", p, e); continue
    print("##", p, "| modified:", d.get("metadata_modified","")[:10], "| title:", d.get("title"))
    for r in d.get("resources", []):
        fmt = r.get("format"); url = r.get("url"); name = r.get("name")
        print("  -", fmt, name, url)
        if fmt and fmt.upper() in ("CSV",):
            fn = os.path.join(OUT, p + "__" + os.path.basename(url.split("?")[0]))
            if not os.path.exists(fn):
                urllib.request.urlretrieve(url, fn)
            print("    saved", fn, os.path.getsize(fn))
