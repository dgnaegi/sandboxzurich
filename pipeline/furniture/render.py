"""Preview renderer (plain python+numpy+PIL, no Blender): contact sheet + compare. python3 -I pipeline/furniture/render.py"""
import json, struct, math, os, glob
import numpy as np
from PIL import Image, ImageDraw
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
D=os.path.join(ROOT,'web/public/models/furniture')
def load(p):
    b=open(p,'rb').read(); jl=struct.unpack('<I',b[12:16])[0]; js=json.loads(b[20:20+jl]); bin_=b[28+jl:]
    bv=js['bufferViews']; n=js['accessors'][0]['count']
    pos=np.frombuffer(bin_,'<f4',n*3,bv[0]['byteOffset']).reshape(-1,3)
    col=np.frombuffer(bin_,'u1',n*4,bv[2]['byteOffset']).reshape(-1,4)[:,:3]
    return pos.reshape(-1,3,3),col.reshape(-1,3,3)[:,0]
def render(p,size=300,yaw=35,pitch=20):
    T,C=load(p); mn=T.reshape(-1,3).min(0); mx=T.reshape(-1,3).max(0)
    c=(mn+mx)/2; hx=max(mx[0]-mn[0],mx[2]-mn[2])*0.8
    a=math.radians(yaw); e=math.radians(pitch)
    Ry=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
    Rx=np.array([[1,0,0],[0,math.cos(e),-math.sin(e)],[0,math.sin(e),math.cos(e)]])
    f=lambda X:(X-c)@Ry.T@Rx.T
    P=f(T)
    G=f(np.array([(-hx,mn[1],-hx),(hx,mn[1],-hx),(hx,mn[1],hx),(-hx,mn[1],hx)]))
    allp=np.vstack([P.reshape(-1,3),G])
    x0,x1,y0,y1=allp[:,0].min(),allp[:,0].max(),allp[:,1].min(),allp[:,1].max()
    ss=size*0.9/max(x1-x0,y1-y0); cx,cy=(x0+x1)/2,(y0+y1)/2
    pt=lambda q:(size/2+(q[0]-cx)*ss,size/2-(q[1]-cy)*ss)
    S2=size*2; img=Image.new('RGB',(size,size),(205,222,235)); d=ImageDraw.Draw(img)
    d.polygon([pt(q) for q in G],fill=(150,150,145))
    L=np.array([-0.3,0.6,-0.7]); L/=np.linalg.norm(L)
    for i in np.argsort(-P[:,:,2].mean(1)):
        t=P[i]; n=np.cross(t[1]-t[0],t[2]-t[0]); ln=np.linalg.norm(n)
        if ln<1e-12: continue
        n/=ln
        if n[2]>0.0: continue
        sh=0.55+0.45*max(0,float(np.dot(n,L)))
        cc=C[i]
        col=(255,243,200) if tuple(cc)==(255,243,200) else tuple(int(min(255,v*sh*1.1)) for v in cc)
        d.polygon([pt(q) for q in t],fill=col)
    return img
if __name__=='__main__':
    man=json.load(open(os.path.join(D,'manifest.json')))
    cols=5; S=320; rows=math.ceil(len(man)/cols)
    sheet=Image.new('RGB',(cols*S,rows*S),'white'); dr=ImageDraw.Draw(sheet)
    for k,m in enumerate(man):
        im=render(os.path.join(D,m['file']),S); x,y=(k%cols)*S,(k//cols)*S
        sheet.paste(im,(x,y)); dr.text((x+6,y+6),f"{m['name']} {m['tris']}t",fill=(0,0,0))
    sheet.save(os.path.join(ROOT,'preview/furniture_sheet.jpg'),quality=85)
    files=json.load(open(os.path.join(ROOT,'pipeline/furniture/ref_files.json'))) if False else sorted(glob.glob(os.path.join(ROOT,'data/raw/photos/furniture/*.jpg')))
    pick=lambda pid:[f for f in files if os.path.basename(f).startswith(pid)][0]
    pairs=[('27765616','hydrant'),('77699402','fountain_trough'),('85689114','pingpong'),('11576149','bench_slat'),('38619681','bench_metal'),('195974501','lamp_classic')]
    W=Image.new('RGB',(1600,3*400),'white'); dd=ImageDraw.Draw(W)
    for k,(pid,nm) in enumerate(pairs):
        r=Image.open(pick(pid)).convert('RGB'); r.thumbnail((400,400))
        mm=render(os.path.join(D,nm+'.glb'),400)
        x=(k%2)*800; y=(k//2)*400
        W.paste(r,(x,y)); W.paste(mm,(x+400,y)); dd.text((x+404,y+4),nm,fill=(0,0,0))
    W.save(os.path.join(ROOT,'preview/furniture_compare.jpg'),quality=85)
