import sys
from PIL import Image
out=sys.argv[1]; files=sys.argv[2:]
ims=[Image.open(f).convert('RGB') for f in files]
H=420
ims=[i.resize((int(i.width*H/i.height),H)) for i in ims]
rows=[];row=[];w=0
for i in ims:
    if w+i.width>1600 and row: rows.append(row);row=[];w=0
    row.append(i);w+=i.width
if row: rows.append(row)
sheet=Image.new('RGB',(1600,H*len(rows)),'black')
for r,row in enumerate(rows):
    x=0
    for i in row: sheet.paste(i,(x,r*H));x+=i.width
sheet.save(out,quality=70)
