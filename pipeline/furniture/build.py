"""Run: /opt/homebrew/bin/blender -b -P pipeline/furniture/build.py  -> web/public/models/furniture/*.glb + manifest.json"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import Model, LAMP
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'web/public/models/furniture')

STONE=0x9d998f; STONE_D=0x7f7b73; WATER=0x5f8c99; CONC=0xaaa8a1; CONC_D=0x8d8b85
WOOD=0xb98a56; WOOD_D=0x9c703f; DARK=0x34383b; GREY=0x7a8085; GREYL=0x9aa0a5
LGREEN=0x7f8f84

def fountain_trough():
    m=Model()
    L,W,H=2.2,0.9,0.78; t=0.14
    m.box((0,0.04,0),(L+0.08,0.08,W+0.08),STONE_D)               # plinth
    m.box((0,0.08+0.03,0),(L-0.2,0.06,W-0.2),STONE_D)             # floor
    m.box((0,0.08+H/2,-W/2+t/2),(L,H,t),STONE)                    # walls
    m.box((0,0.08+H/2, W/2-t/2),(L,H,t),STONE)
    m.box((-L/2+t/2,0.08+H/2,0),(t,H,W-2*t),STONE)
    m.box(( L/2-t/2,0.08+H/2,0),(t,H,W-2*t),STONE)
    m.box((0,0.08+H-0.14,0),(L-2*t,0.02,W-2*t),WATER)             # water surface
    m.box((0,0.08+H+0.015,-W/2+t/2),(L+0.04,0.03,t+0.03),STONE_D) # coping
    m.box((0,0.08+H+0.015, W/2-t/2),(L+0.04,0.03,t+0.03),STONE_D)
    sx=-L/2+0.45; B=0.08+H; zz=W/2-0.25                            # Brunnenstock on rear wall
    m.box((sx,B+0.1,zz),(0.4,0.2,0.4),STONE)
    m.box((sx,B+0.4,zz),(0.26,0.4,0.26),STONE)
    m.box((sx,B+0.65,zz),(0.34,0.1,0.34),STONE_D)
    m.cyl(sx,B+0.7,zz,0.14,0.0,0.22,STONE,seg=8)
    m.cyl(sx,B+0.28,zz-0.13,0.035,0.035,0.28,GREY,seg=6,rx=-90)    # Roehre pointing -Z
    m.cyl(sx,0.08+H-0.05,-0.02,0.012,0.012,0.18,WATER,seg=4)       # water jet
    return m
def fountain_round():
    m=Model()
    m.cyl(0,0,0,0.5,0.5,0.1,CONC_D,seg=12)
    m.cyl(0,0.1,0,0.3,0.2,0.6,CONC,seg=12)
    m.cyl(0,0.7,0,0.25,0.8,0.42,CONC,seg=14)
    m.cyl(0,1.12,0,0.8,0.8,0.0001,CONC_D,seg=14,cap0=False) if False else None
    m.cyl(0,1.1,0,0.8,0.8,0.03,CONC_D,seg=14)
    m.cyl(0,1.13,0,0.68,0.68,0.01,WATER,seg=14)
    m.cyl(0,1.13,0,0.1,0.07,0.6,CONC_D,seg=8)
    m.cyl(0,1.73,0,0.08,0.01,0.1,GREY,seg=8)
    m.cyl(0,1.2,0.07,0.025,0.025,0.2,GREY,seg=6,rx=-90)
    return m
def fountain_drink():
    m=Model()
    m.cyl(0,0,0,0.26,0.2,0.12,CONC_D,seg=8)
    m.cyl(0,0.12,0,0.16,0.12,0.6,CONC,seg=8)
    m.cyl(0,0.72,0,0.14,0.28,0.12,CONC,seg=10)
    m.cyl(0,0.84,0,0.28,0.28,0.03,CONC_D,seg=10)
    m.cyl(0,0.87,0,0.2,0.2,0.01,WATER,seg=10)
    m.cyl(0,0.87,0.1,0.025,0.025,0.2,GREYL,seg=6)
    m.cyl(0,1.07,0.1,0.025,0.025,0.1,GREYL,seg=6,rx=-90)
    m.cyl(0,0.9,0.0,0.03,0.03,0.12,GREYL,seg=6)
    return m
def slats(m,x0,x1,zc,y,sy,sz,n,gap,color,rx=0,dy=0):
    L=x1-x0
    for i in range(n):
        m.box(((x0+x1)/2,y+i*dy,zc+i*(sz+gap)*(1 if dy==0 else 0)),(L,sy,sz),color,rx=rx)
def bench_slat():
    m=Model(); L=1.9
    for sx in (-0.7,0.7):
        m.cyl(sx,0,0,0.23,0.22,0.42,CONC,seg=10)                       # concrete cylinder foot (Schanzengraben type)
        m.cyl(sx,0.42,0,0.24,0.24,0.03,CONC_D,seg=10)
        m.box((sx,0.62,0.2),(0.1,0.5,0.08),CONC,rx=-14)                # back support
    z0=-0.2
    for i in range(5):                                                 # seat slats
        m.box((0,0.455,z0+i*0.085),(L,0.04,0.07),WOOD)
    for i in range(3):                                                 # curved-ish back slats
        y=0.62+i*0.11
        m.box((0,y,0.215+(y-0.5)*-0.25),(L,0.08,0.03),WOOD_D,rx=-14)
    return m
def bench_metal():
    m=Model(); L=1.8
    for sx in (-0.8,0.8):
        m.box((sx,0.2,-0.17),(0.05,0.4,0.05),DARK)
        m.box((sx,0.2, 0.2),(0.05,0.4,0.05),DARK)
        m.box((sx,0.42,0.02),(0.05,0.04,0.5),DARK)
        m.box((sx,0.62,0.24),(0.05,0.5,0.04),DARK,rx=-12)
        m.box((sx,0.62,-0.1),(0.05,0.04,0.34),DARK)                    # armrest
        m.box((sx,0.5,-0.25),(0.05,0.24,0.04),DARK) if False else None
    for i in range(5): m.box((0,0.455,-0.2+i*0.1),(L,0.03,0.08),LGREEN)
    for i in range(3):
        y=0.6+i*0.12; m.box((0,y,0.23-(y-0.5)*0.2),(L,0.09,0.025),LGREEN,rx=-12)
    return m
def bin_():
    m=Model()
    m.cyl(0,0,0,0.2,0.2,0.05,DARK,seg=10)
    m.cyl(0,0.05,0,0.21,0.21,0.8,0x555b5e,seg=10)
    m.cyl(0,0.5,0,0.215,0.215,0.06,0x9aa0a3,seg=10,cap0=False,cap1=False)
    m.cyl(0,0.85,0,0.21,0.235,0.08,0x9aa0a3,seg=10,cap0=False)
    m.cyl(0,0.93,0,0.235,0.235,0.03,0x9aa0a3,seg=10,cap0=False)
    m.cyl(0,0.933,0,0.17,0.17,0.005,0x1d1f20,seg=10)                  # dark opening
    m.box((0,0.97,0.0),(0.1,0.03,0.4),0x9aa0a3) if False else None
    m.box((0,0.76,-0.215),(0.12,0.012,0.012),0xe8e8e8) if False else None
    return m
def hydrant():
    m=Model(); HG=0x858b90; HD=0x5c6266
    m.cyl(0,0,0,0.13,0.13,0.05,HD,seg=8)
    m.cyl(0,0.05,0,0.095,0.085,0.45,HG,seg=8)
    m.cyl(0,0.38,0,0.1,0.1,0.04,HD,seg=8)
    m.cyl(0,0.5,0,0.085,0.1,0.18,HG,seg=8)
    m.cyl(0,0.68,0,0.1,0.07,0.06,HD,seg=8)
    m.cyl(0,0.74,0,0.07,0.0,0.07,HG,seg=8)
    m.cyl(0,0.7,0,0.02,0.02,0.1,HD,seg=4) if False else None
    for sx in (-1,1): m.cyl(sx*0.12,0.58,0,0.045,0.045,0.1,HD,seg=6,rz=90*-sx*-1 if False else 0) if False else None
    for sx in (-1,1):
        m.cyl(sx*0.05,0.58,0,0.032,0.032,0.1,HD,seg=6,rz=-90*sx)
    m.cyl(0,0.56,-0.06,0.065,0.065,0.1,HD,seg=8,rx=-90)
    return m
def pingpong():
    m=Model(); L,W=2.74,1.525
    m.box((0,0.70,0),(L,0.12,W),CONC)
    m.box((0,0.765,0),(L,0.01,0.02),0xe8e8e8)
    m.box((0,0.34,0),(0.5,0.56,0.3),CONC_D)                       # central pedestal
    for r in (28,-28): m.box((0,0.08,0),(0.14,0.14,2.3),CONC_D,ry=r)  # X-shaped foot beams
    for sx in (-1,1): m.box((sx*0.6,0.45,0),(0.12,0.12,1.2),CONC_D) if False else None
    m.box((0,0.84,0),(0.02,0.14,W+0.2),0xdcdcd8)
    for sz in (-1,1): m.box((0,0.84,sz*(W/2+0.1)),(0.03,0.16,0.03),DARK)
    return m
def lamp_cable():
    m=Model(); G=0x6c7277
    m.box((0,-0.01,0),(0.7,0.02,0.02),DARK)
    m.cyl(0,-0.4,0,0.015,0.015,0.4,DARK,seg=6)
    m.cyl(0,-0.52,0,0.1,0.07,0.12,G,seg=10)
    m.cyl(0,-0.62,0,0.28,0.12,0.1,G,seg=12,cap1=False)
    m.cyl(0,-0.64,0,0.24,0.24,0.02,G,seg=12)
    m.cyl(0,-0.655,0,0.2,0.2,0.012,LAMP,seg=12,cap1=False) if False else None
    m.cyl(0,-0.662,0,0.21,0.21,0.02,LAMP,seg=12)
    return m
def lamp_mast():
    m=Model(); G=0x707579
    m.cyl(0,0,0,0.2,0.16,0.12,G,seg=8)
    m.cyl(0,0.12,0,0.11,0.065,6.4,G,seg=8,cap1=True)
    m.box((0,6.5,-0.55),(0.07,0.07,1.3),G,rx=-8)                  # boom rising slightly
    m.box((0,6.64,-1.15),(0.16,0.14,0.8),G)                        # luminaire housing
    m.box((0,6.565,-1.15),(0.12,0.02,0.7),LAMP)
    m.box((0,6.71,-1.15),(0.18,0.02,0.84),0x5a6064)
    return m
def lamp_classic():
    m=Model(); K=0x2a2f2d
    m.cyl(0,0,0,0.2,0.16,0.15,K,seg=8)
    m.cyl(0,0.15,0,0.15,0.08,0.8,K,seg=8)
    m.cyl(0,0.95,0,0.09,0.09,0.06,K,seg=8)
    m.cyl(0,1.01,0,0.055,0.04,2.4,K,seg=8)
    m.cyl(0,3.41,0,0.09,0.09,0.05,K,seg=8)
    m.cyl(0,3.46,0,0.12,0.19,0.07,K,seg=6)
    m.cyl(0,3.53,0,0.19,0.23,0.5,LAMP,seg=6,cap0=False,cap1=False)
    for i in range(6):
        import math; a=math.radians(60*i+30)
        m.box((0.22*math.cos(a),3.78,0.22*math.sin(a)),(0.025,0.54,0.025),K,ry=-60*i)
    m.cyl(0,4.03,0,0.3,0.05,0.2,K,seg=6)
    m.cyl(0,4.23,0,0.03,0.0,0.14,K,seg=6)
    return m
def bollard():
    m=Model()
    m.cyl(0,0,0,0.08,0.08,0.85,0x80868a,seg=8)
    m.cyl(0,0.85,0,0.08,0.05,0.05,0x80868a,seg=8)
    m.cyl(0,0.62,0,0.083,0.083,0.1,0xe9e9e4,seg=8,cap0=False,cap1=False)
    return m
def sign_pole():
    m=Model(); G=0x8a9094
    m.cyl(0,0,0,0.035,0.035,3.3,G,seg=8)
    m.cyl(0,3.3,0,0.04,0.0,0.04,G,seg=8)
    for y in (2.4,3.0): m.box((0,y,0.0),(0.075,0.03,0.075),0x5f656a)
    return m

ITEMS=[('fountain_trough',fountain_trough,400),('fountain_round',fountain_round,400),('fountain_drink',fountain_drink,400),
 ('bench_slat',bench_slat,400),('bench_metal',bench_metal,400),('bin',bin_,400),('hydrant',hydrant,400),
 ('pingpong',pingpong,400),('lamp_cable',lamp_cable,250),('lamp_mast',lamp_mast,250),('lamp_classic',lamp_classic,400),
 ('bollard',bollard,400),('sign_pole',sign_pole,250)]
os.makedirs(OUT,exist_ok=True)
man=[]
for name,fn,cap in ITEMS:
    tris,size=fn().write_glb(os.path.join(OUT,name+'.glb')) if False else (None,None)
    m=fn(); tris,size=m.write_glb(os.path.join(OUT,name+'.glb'))
    kb=os.path.getsize(os.path.join(OUT,name+'.glb'))
    flag='' if tris<=cap and kb<30000 else '  OVER BUDGET'
    print(f'{name:16s} tris={tris:4d} size={[round(s,2) for s in size]} {kb}B{flag}')
    man.append({"name":name,"file":name+'.glb',"tris":tris,"size":[round(s,3) for s in size]})
json.dump(man,open(os.path.join(OUT,'manifest.json'),'w'),indent=1)
