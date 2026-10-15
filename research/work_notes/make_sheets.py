import json, os
from PIL import Image, ImageDraw, ImageFont
ROOT='/Users/danielgnagi/gtazurich'
t=json.load(open(f'{ROOT}/research/buildings/testarea.json'))
v=json.load(open(f'{ROOT}/research/buildings/visual_notes.json'))
todo=[]
for b in t:
    key=f"{b['street']} {b['nr']}"
    if key in v or '_' in key[:1]: continue
    ph=[p for p in b.get('photos',[]) if os.path.exists(os.path.join(ROOT,p['file']))]
    if not ph: continue
    pick=next((p for p in ph if p.get('crop_note') or p.get('source')=='Panoramax'), ph[0])
    todo.append((key, os.path.join(ROOT,pick['file'])))
todo.sort()
json.dump(todo, open(f'{ROOT}/research/work_notes/todo.json','w'), ensure_ascii=False, indent=0)
print('todo', len(todo), 'of which no-photo missing:', sum(1 for b in t if f"{b['street']} {b['nr']}" not in v) - len(todo))
font=None
for f in ['/System/Library/Fonts/Supplemental/Arial Bold.ttf','/Library/Fonts/Arial Bold.ttf']:
    if os.path.exists(f): font=ImageFont.truetype(f,22); break
if font is None: font=ImageFont.load_default()
W=360; H=270
for s in range(0,len(todo),12):
    chunk=todo[s:s+12]
    rows=(len(chunk)+2)//3
    sheet=Image.new('RGB',(W*3+20,(H+30)*rows+10),(30,30,30))
    d=ImageDraw.Draw(sheet)
    for i,(key,path) in enumerate(chunk):
        try:
            im=Image.open(path).convert('RGB')
            im.thumbnail((W,H-10))
        except Exception as e:
            im=Image.new('RGB',(W,H-10),(80,0,0))
        x=(i%3)*(W+10); y=(i//3)*(H+30)
        d.rectangle([x,y,x+W,y+30],fill=(0,0,0))
        d.text((x+6,y+3),f"{i+1}. {key}",fill=(255,255,0),font=font)
        sheet.paste(im,(x,y+30))
    out=f'{ROOT}/research/work_notes/sheet_{s//12+1:02d}.jpg'
    sheet.save(out,quality=85)
    print(out, [k for k,_ in chunk])
