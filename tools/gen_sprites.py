#!/usr/bin/env python3
# Nico — pixel art estilo "line-art" para OLED: contorno branco, interior preto,
# manchas laranja pontilhadas, detalhes brancos. Olhos são desenhados no firmware
# (âncoras exportadas), assim o humor muda sem multiplicar sprites.
import numpy as np, os
W, H, GND = 44, 44, 42
yy, xx = np.mgrid[0:H, 0:W]
DITHER = ((xx % 2 == 0) & (yy % 2 == 0)) | ((xx % 4 == 1) & (yy % 4 == 3))

def E(cx,cy,rx,ry): return ((xx-cx)/rx)**2+((yy-cy)/ry)**2 <= 1.0
def R(x0,y0,x1,y1): return (xx>=x0)&(xx<=x1)&(yy>=y0)&(yy<=y1)
def T(p,q,r):
    a,b,c=map(np.array,(p,q,r))
    d1=(xx-b[0])*(a[1]-b[1])-(a[0]-b[0])*(yy-b[1])
    d2=(xx-c[0])*(b[1]-c[1])-(b[0]-c[0])*(yy-c[1])
    d3=(xx-a[0])*(c[1]-a[1])-(c[0]-a[0])*(yy-a[1])
    return ~(((d1<0)|(d2<0)|(d3<0))&((d1>0)|(d2>0)|(d3>0)))
def L(pts, t=0):
    m=np.zeros((H,W),bool)
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
        n=int(max(abs(x1-x0),abs(y1-y0)))*2+1
        for i in range(n+1):
            x=round(x0+(x1-x0)*i/n); y=round(y0+(y1-y0)*i/n)
            m |= ((xx-x)**2+(yy-y)**2 <= t*t) if t>0 else ((xx==x)&(yy==y))
    return m
def outline(m):
    er=m.copy()
    er[1:,:]&=m[:-1,:]; er[:-1,:]&=m[1:,:]; er[:,1:]&=m[:,:-1]; er[:,:-1]&=m[:,1:]
    return m&~er

class Cat:
    def __init__(s): s.sil=np.zeros((H,W),bool); s.orange=np.zeros((H,W),bool); s.lines=np.zeros((H,W),bool); s.black=np.zeros((H,W),bool)
    def body(s,m): s.sil|=m
    def org(s,m): s.orange|=m
    def ln(s,m): s.lines|=m
    def stripe(s,m): s.black|=m
    def render(s):
        img = outline(s.sil) | s.lines
        mask = s.sil | s.lines
        return img, mask

# ---------- cabeça de frente (Nico) ----------
def head(c, hx, hy):
    eL=T((hx-11,hy-2),(hx-9,hy-15),(hx-3,hy-7)); eR=T((hx+3,hy-7),(hx+9,hy-15),(hx+11,hy-2))
    hd=E(hx,hy,11,9)
    c.body(hd|eL|eR)
    c.org(eL|eR)
    c.org(hd & (yy<=hy-1))                                  # topo laranja
    c.org(E(hx-5,hy+1,4.5,3.5)|E(hx+5,hy+1,4.5,3.5))        # manchas dos olhos
    c.org(E(hx-10,hy+3,2,3)|E(hx+10,hy+3,2,3))              # bochechas laterais
    blaze = R(hx-1,hy-9,hx+1,hy+2) | T((hx-3,hy+3),(hx+3,hy+3),(hx,hy-1))
    c.orange &= ~blaze                                       # faixa branca no meio
    c.ln(R(hx-3,hy-8,hx-3,hy-6)|R(hx,hy-8,hx,hy-7)|R(hx+3,hy-8,hx+3,hy-6))   # listrinhas da testa
    # nariz + boca "w"
    c.ln(R(hx-1,hy+4,hx+1,hy+4)|R(hx,hy+5,hx,hy+5))
    c.ln(L([(hx,hy+6),(hx-1,hy+7),(hx-3,hy+6)])|L([(hx,hy+6),(hx+1,hy+7),(hx+3,hy+6)]))
    # bigodes passando do contorno
    c.ln(R(hx-15,hy+3,hx-9,hy+3)|R(hx-15,hy+5,hx-9,hy+5))      # bigodes cruzando o contorno
    c.ln(R(hx+9,hy+3,hx+15,hy+3)|R(hx+9,hy+5,hx+15,hy+5))
    return (hx-5, hx+5, hy+1)                                # âncora dos olhos

def tail_sit(c, frame):
    if frame==0: path=[(31,40),(36,39),(39,35),(39,30),(37,27)]
    elif frame==1: path=[(31,40),(37,40),(40,36),(41,31),(40,27)]
    else: path=[(31,40),(36,38),(38,33),(37,28),(34,26)]
    m=L(path,1.6); c.body(m); c.org(m)
    for (x,y) in path[1:-1]: c.stripe(R(x-2,y,x+2,y))       # anéis

def sit(frame=0, groom=False):
    c=Cat(); hx,hy=22,15
    tail_sit(c,frame)
    bd=E(22,32,10,10)|R(13,32,31,41)                         # corpo
    hl=E(14,37,5,5)|E(30,37,5,5)                             # coxas
    c.body(bd|hl); c.org((bd|hl) & ~E(22,31,5,10))           # lados laranja, peito branco
    c.stripe(R(13,30,15,30)|R(29,30,31,30)|R(12,34,14,34)|R(30,34,32,34))
    # patas da frente (linhas) e dedinhos
    c.ln(R(18,31,18,41)|R(26,31,26,41)|R(22,35,22,41))       # patas
    a=head(c,hx,hy)
    c.ln(R(16,24,28,24))                                       # gola
    if groom:
        paw=E(29,23,3,3); c.body(paw); c.ln(L([(27,32),(29,26)]))
    return c.render(), a

def loaf(frame=0):
    c=Cat(); hx,hy=22,23
    bd=E(22,36,16,7)&(yy<=42); c.body(bd); c.org(bd & ~E(22,37,6,6))
    t=L([(8,40),(14,42),(28,42)],1.3); c.body(t); c.org(t)
    c.stripe(R(9,34,11,34)|R(33,34,35,34))
    a=head(c,hx,hy)
    return c.render(), a

def eat(frame=0):
    c=Cat(); hx,hy=22,21+frame
    tail_sit(c,2)
    bd=E(22,34,11,8)|R(12,34,32,41); c.body(bd); c.org(bd & ~E(22,35,5,8))
    c.ln(L([(19,36),(19,41)])|L([(25,36),(25,41)]))
    a=head(c,hx,hy)
    bowl=T((10,37),(34,37),(22,49))&(yy<=41); c.body(bowl)          # tigela
    c.ln(R(14,36,16,36)|R(20,35,23,35)|R(27,36,29,36))              # ração
    return c.render(), a

def walk(frame=0):
    c=Cat(); hx,hy=31,15
    t=[[(10,27),(6,22),(5,15),(8,11)],[(10,27),(5,23),(4,16),(6,11)],[(10,27),(6,21),(6,14),(10,10)],[(10,27),(5,22),(5,15),(8,11)]][frame%4]
    tm=L(t,1.6); c.body(tm); c.org(tm)
    for (x,y) in t[1:-1]: c.stripe(R(x-2,y,x+2,y))
    bd=E(20,29,12,6); c.body(bd); c.org(bd & (yy<=30))
    c.stripe(R(14,24,14,27)|R(19,23,19,26)|R(24,24,24,27))
    lift=[(0,2),(2,0),(1,1),(2,0)][frame%4]
    for i,x in enumerate([28,24,15,11]):
        o=lift[i%2]; lg=R(x-1,33,x+1,41-o); c.body(lg)
        if i>=2: c.org(lg)
    nk=E(28,24,5,6); c.body(nk); c.org(nk&(xx<=27))
    a=head(c,hx,hy)
    return c.render(), a

def stretch():
    c=Cat(); hx,hy=31,28
    tm=L([(9,26),(5,19),(5,12),(8,9)],1.6); c.body(tm); c.org(tm)
    hb=E(12,30,7,7); c.body(hb); c.org(hb)
    bd=E(22,35,10,5); c.body(bd); c.org(bd&(yy<=34))
    c.body(R(9,34,12,41)); c.org(R(9,34,12,41))
    c.body(R(30,38,41,41)); c.ln(L([(35,38),(35,41)]))
    a=head(c,hx,hy)
    return c.render(), a

def sleep(frame=0):
    c=Cat()
    bd=E(23,36-frame,16,6); c.body(bd); c.org(bd)
    hd=E(12,35,7,6); ear1=T((6,33),(6,26),(11,31)); ear2=T((12,30),(15,25),(17,31))
    c.body(hd|ear1|ear2); c.org((hd|ear1|ear2)&~R(10,35,14,40))
    t=L([(37,37),(35,31),(26,30)],1.4); c.body(t); c.org(t)
    c.ln(L([(8,35),(10,36),(12,35)])|L([(14,35),(16,36)]))   # olhinhos fechados
    c.ln(R(12,38,13,38))
    c.stripe(R(22,31,22,34)|R(27,31,27,34)|R(32,32,32,35))
    return c.render(), None

FRONT = {
 'SIT1':sit(0), 'SIT2':sit(1), 'SIT3':sit(2), 'GROOM':sit(0,True),
 'LOAF':loaf(), 'EAT1':eat(0), 'EAT2':eat(1),
 'WALK1':walk(0),'WALK2':walk(1),'WALK3':walk(2),'WALK4':walk(3),
 'STRETCH':stretch(), 'SLEEP1':sleep(0), 'SLEEP2':sleep(1),
}

def mini():                       # cabecinha compacta p/ jogos e relógio (~19x18)
    c=Cat(); hx,hy=9,11
    hd=E(hx,hy,7,5.5); eL=T((hx-7,hy-1),(hx-6,hy-10),(hx-2,hy-4)); eR=T((hx+2,hy-4),(hx+6,hy-10),(hx+7,hy-1))
    c.body(hd|eL|eR); c.org(eL|eR|(hd&(yy<=hy-1)))
    c.orange&=~R(hx,hy-6,hx,hy+1)
    c.ln(R(hx,hy+2,hx,hy+2)|R(hx-1,hy+3,hx-1,hy+3)|R(hx+1,hy+3,hx+1,hy+3))
    img,m=c.render()
    return img[0:18,0:19], m[0:18,0:19], (hx-3,hx+3,hy)

# --------- olhos (mesma lógica do firmware) ---------
def eyes(img, ex, ey, kind):
    for x in (ex[0],ex[1]):
        img[ey-2:ey+3, x-3:x+4]=False
        if kind=='sleepy':
            img[ey-1, x-2:x+3]=True; img[ey, x-1:x+2]=True
        elif kind=='open':
            img[ey-1:ey+2, x-1:x+2]=True; img[ey-1,x-1]=False
        elif kind=='wide':
            img[ey-2:ey+2, x-2:x+2]=True; img[ey-2,x-2]=False
        elif kind=='closed':
            img[ey, x-2:x+3]=True
        elif kind=='happy':
            for dx,dy in ((-2,1),(-1,0),(0,-1),(1,0),(2,1)): img[ey+dy,x+dx]=True

def pack(a):
    h,w=a.shape; rb=(w+7)//8; out=[]
    for y in range(h):
        for b in range(rb):
            v=0
            for bit in range(8):
                x=b*8+bit
                if x<w and a[y,x]: v|=1<<(7-bit)
            out.append(v)
    return out
def arr(f,name,a): f.write(f'static const uint8_t {name}[] PROGMEM = {{'+','.join(map(str,pack(np.ascontiguousarray(a))))+'};\n')

def emit():
    with open('src/sprites.h','w') as f:
        f.write('// Gerado por tools/gen_sprites.py — Nico line-art\n#pragma once\n#include <Arduino.h>\n')
        f.write(f'#define NICO_W {W}\n#define NICO_H {H}\n#define NICO_GND {GND}\n')
        for n,((img,m),a) in FRONT.items():
            arr(f,f'NICO_{n}_R',img); arr(f,f'NICO_{n}_RM',m)
            arr(f,f'NICO_{n}_L',img[:,::-1]); arr(f,f'NICO_{n}_LM',m[:,::-1])
            if a: f.write(f'#define NICO_{n}_EYE {a[0]},{a[1]},{a[2]}\n')
            else: f.write(f'#define NICO_{n}_EYE -1,-1,-1\n')
        mi,mm,ma=mini()
        f.write(f'#define MINI_W {mi.shape[1]}\n#define MINI_H {mi.shape[0]}\n#define MINI_EYE {ma[0]},{ma[1]},{ma[2]}\n')
        arr(f,'MINI_IMG',mi); arr(f,'MINI_MASK',mm)
    print('src/sprites.h ok')

def preview():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    items=list(FRONT.items()); cols=5; rows=(len(items)+cols-1)//cols
    fig,axs=plt.subplots(rows,cols,figsize=(cols*2.3,rows*2.4))
    kinds=['sleepy','open','wide','happy','closed']
    for i,(ax,(name,((img,m),a))) in enumerate(zip(axs.ravel(),items)):
        im=img.copy()
        if a: eyes(im,(a[0],a[1]),a[2],kinds[i%5] if name.startswith('SIT') else 'sleepy')
        c=np.zeros((H,W)); c[im]=1
        ax.imshow(c,cmap='gray',interpolation='nearest',vmin=0,vmax=1); ax.set_title(name,fontsize=8); ax.axis('off')
    for ax in axs.ravel()[len(items):]: ax.axis('off')
    plt.tight_layout(); plt.savefig('tools/sprites_preview.png',dpi=110,facecolor='#333')

if __name__=='__main__': emit(); preview(); print('preview ok')
