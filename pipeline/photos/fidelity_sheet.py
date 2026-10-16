"""Pair sheets: photo left, game right. usage: fidelity_sheet.py gamedir outprefix per_sheet ids..."""
import json, sys
from PIL import Image, ImageDraw
gdir, out, per = sys.argv[1], sys.argv[2], int(sys.argv[3])
ids = [int(i) for i in sys.argv[4:]]
cand = {c['id']: c for c in json.load(open('research/fidelity_cand.json'))}
W, H = 400, 300
for s in range(0, len(ids), per):
    ch = ids[s:s + per]
    sh = Image.new('RGB', (2 * W, len(ch) * H), 'white')
    for j, i in enumerate(ch):
        a = Image.open(cand[i]['file']).convert('RGB').resize((W, H))
        b = Image.open(f'{gdir}/game_{i}.png').convert('RGB').resize((W, H))
        sh.paste(a, (0, j * H)); sh.paste(b, (W, j * H))
        ImageDraw.Draw(sh).text((4, j * H + 4), f'#{i}', fill=(255, 255, 0))
    sh.save(f'{out}_{s // per + 1}.jpg', quality=72)
