import json,sys
from PIL import Image,ImageDraw
R='/Users/danielgnagi/gtazurich'
meta=json.load(open(R+'/research/places_k45/places_photos.json'))
for slug in sys.argv[1:]:
    recs=meta.get(slug,[])
    if not recs: print(slug,'none');continue
    C,W,H=4,380,285
    rows=(len(recs)+C-1)//C
    s=Image.new('RGB',(C*W,rows*H),(25,25,25));d=ImageDraw.Draw(s)
    for i,r in enumerate(recs):
        im=Image.open(R+'/'+r['file']).convert('RGB');im.thumbnail((W-4,H-4))
        x,y=(i%C)*W,(i//C)*H;s.paste(im,(x+2,y+2));d.rectangle([x+2,y+2,x+30,y+16],fill=(0,0,0));d.text((x+6,y+3),str(i+1),fill=(255,220,0))
    s.save(f'{R}/preview/ref_k45_{slug}.jpg','JPEG',quality=78);print(slug,len(recs))
