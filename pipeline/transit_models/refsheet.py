import sys,glob,os
from PIL import Image,ImageDraw
fs=sorted(glob.glob('data/raw/photos/transit/*'))
fs=[f for f in fs if 'AC_Cobra' not in f and 'AH-1W' not in f and 'ZBT021' not in f]
W,H=320,214;cols=5;rows=(len(fs)+cols-1)//cols
S=Image.new('RGB',(W*cols,H*rows),'white');d=ImageDraw.Draw(S)
for i,f in enumerate(fs):
    im=Image.open(f).convert('RGB');im.thumbnail((W,H-12))
    x,y=(i%cols)*W,(i//cols)*H;S.paste(im,(x,y));d.text((x+2,y+H-11),f"{i}:"+os.path.basename(f)[:44],fill='black')
S.save('/private/tmp/claude-501/-Users-danielgnagi-sandboxzurich/2c85f10e-b4e1-4c95-8bd3-e132013d6298/scratchpad/refs.jpg',quality=80)
