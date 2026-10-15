"""python3 compare.py <renderdir> -> preview/transit_compare.jpg (render left, reference photo right)"""
import sys; from PIL import Image, ImageDraw
d = sys.argv[1]; R = 'data/raw/photos/transit/'
rows = [('tram_cobra', '34', 'Zurich_Be_5-6_Cobra_3002_Letzistrasse.jpg'), ('tram_cobra', 'front', 'CobraTramZ_rich.JPG'),
        ('tram_flexity', '34', 'VBZ_Tram_16_Weinbergstrasse.jpg'), ('trolleybus', '34', 'Verkehrsbetriebe_Z_rich_560_ZH730560_-_Neoplan_Centroliner_Evolution.jpg')]
W, H = 560, 320; S = Image.new('RGB', (W*2, H*len(rows)), 'white'); dr = ImageDraw.Draw(S)
for i, (n, v, ph) in enumerate(rows):
    a = Image.open(f'{d}/{n}_{v}.png').convert('RGB'); a = a.crop((0, 0, a.width, a.height)); a = a.resize((W, int(W*a.height/a.width)))
    b = Image.open(R+ph).convert('RGB'); b.thumbnail((W, H))
    S.paste(a, (0, i*H)); S.paste(b, (W, i*H)); dr.text((4, i*H+3), f'model {n} {v}', fill='white'); dr.text((W+4, i*H+3), ph[:50], fill='yellow')
S.save('preview/transit_compare.jpg', quality=85)
