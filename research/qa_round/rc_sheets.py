import json,os
from PIL import Image,ImageDraw
import sys
F=sys.argv[1] if len(sys.argv)>1 else 'rc_shots.json';OFF=int(sys.argv[2]) if len(sys.argv)>2 else 0
S=json.load(open('research/qa_round/'+F))
W,H=400,300
def fit(im):
    im=im.convert('RGB');r=max(W/im.width,H/im.height);im=im.resize((int(im.width*r)+1,int(im.height*r)+1));l=(im.width-W)//2;t=(im.height-H)//2;return im.crop((l,t,l+W,t+H))
for si in range(0,len(S),6):
    ch=S[si:si+6];sh=Image.new('RGB',(1600,3*(H+16)),'white');d=ImageDraw.Draw(sh)
    for k,s in enumerate(ch):
        cx=(k%2)*800;cy=(k//2)*(H+16)
        g=f"research/qa_round/game/game_{s['id']}.png"
        try: a=fit(Image.open(s['file']));b=fit(Image.open(g))
        except Exception as e: print('miss',s['id'],e);continue
        sh.paste(a,(cx,cy+16));sh.paste(b,(cx+400,cy+16))
        d.text((cx+2,cy+2),f"{s['id']} {s['place']} ({s['x']:.0f},{s['y']:.0f}) h{s['hdg']}  foto | spiel",fill='black')
    sh.save(f"preview/rc_{si//6+1+OFF}.jpg",quality=80)
print('ok')
