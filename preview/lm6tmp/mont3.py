import json,os
from PIL import Image,ImageDraw
items=[]
for p in range(3):
    for i,x in enumerate(json.load(open(f'x{p}.json'))): items.append((x['n'],f'r2/s{p}_{i}.jpg'))
items.sort()
for k in range(0,len(items),12):
    sh=items[k:k+12]; im=Image.new('RGB',(1600,675),'#111')
    for j,(n,f) in enumerate(sh):
        if not os.path.exists(f): continue
        t=Image.open(f).convert('RGB').resize((400,225)); d=ImageDraw.Draw(t);d.rectangle([0,0,170,12],fill='#000');d.text((2,0),n[:34],fill='#ff0')
        im.paste(t,((j%4)*400,(j//4)*225))
    im.save(f'../lm6_check_{k//12}.jpg',quality=80)
