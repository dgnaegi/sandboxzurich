import json,glob,os,sys
from PIL import Image,ImageDraw
items=[]
for p in range(3):
    v=json.load(open(f'w{p}.json'))
    for i,x in enumerate(v):
        f=f'r1/s{p}_{i}.jpg'
        items.append((x['n'],f))
items.sort(key=lambda t:t[0])
pre=sys.argv[1]; 
sheets=[items[i:i+12] for i in range(0,len(items),12)]
for k,sh in enumerate(sheets):
    im=Image.new('RGB',(1600,675),'#111')
    for j,(n,f) in enumerate(sh):
        if not os.path.exists(f): continue
        t=Image.open(f).convert('RGB').resize((400,225))
        d=ImageDraw.Draw(t);d.rectangle([0,0,170,12],fill='#000');d.text((2,0),n[:34],fill='#ff0')
        im.paste(t,((j%4)*400,(j//4)*225))
    im.save(f'../{pre}_{k}.jpg',quality=80)
print(len(sheets))
