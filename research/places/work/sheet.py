import sys,glob,os
from PIL import Image,ImageDraw
P='/Users/danielgnagi/sandboxzurich/data/raw/photos/places'
def sheet(place,files,out,cols=4,w=400):
    ims=[]
    for f in files:
        try:im=Image.open(f).convert('RGB');im.thumbnail((w,int(w*0.75)));ims.append((os.path.relpath(f,P+'/'+place),im))
        except Exception as e:pass
    rows=(len(ims)+cols-1)//cols;h=int(w*0.75)
    S=Image.new('RGB',(cols*w,rows*h),'white');d=ImageDraw.Draw(S)
    for i,(n,im) in enumerate(ims):
        x,y=(i%cols)*w,(i//cols)*h;S.paste(im,(x,y));d.rectangle([x,y,x+60,y+14],fill='black');d.text((x+2,y+1),n.replace('.jpg',''),fill='white')
    S.save(out,quality=70)
if __name__=='__main__':
    place=sys.argv[1];files=sorted(glob.glob(f'{P}/{place}/*.jpg')+glob.glob(f'{P}/{place}/pmx/*.jpg'))
    sheet(place,files[int(sys.argv[2]):int(sys.argv[3])],sys.argv[4])
