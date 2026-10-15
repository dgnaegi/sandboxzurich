"""python3 sheet.py <renderdir> : contact sheet -> preview/transit_sheet.jpg"""
import sys; from PIL import Image, ImageDraw
d = sys.argv[1]; names = ['tram_cobra', 'tram_flexity', 'trolleybus']; views = ['side', '34', 'front']
W, H = 520, 176; S = Image.new('RGB', (W*3, H*3), 'white'); dr = ImageDraw.Draw(S)
for r, n in enumerate(names):
    for c, v in enumerate(views):
        S.paste(Image.open(f'{d}/{n}_{v}.png').convert('RGB').resize((W, H)), (c*W, r*H)); dr.text((c*W+4, r*H+3), f'{n} {v}', fill='white')
S.save('preview/transit_sheet.jpg', quality=85)
