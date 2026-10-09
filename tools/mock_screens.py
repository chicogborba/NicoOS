#!/usr/bin/env python3
# Gera mockups das telas do NicoOS (128x64 ampliado) para o README -> img/screen_*.png
import numpy as np, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import gen_sprites as G

W, H = 128, 64
def canvas(): return Image.new('1', (W, H), 0)

def blit(img, spr, mask, x, y):
    a = np.array(img, dtype=bool)
    h, w = spr.shape
    for yy in range(h):
        for xx in range(w):
            X, Y = x+xx, y+yy
            if 0 <= X < W and 0 <= Y < H and mask[yy, xx]:
                a[Y, X] = spr[yy, xx]
    return Image.fromarray(a)

def room(d):
    for y in range(4, 52, 8):
        for x in range(4 if (y//8) % 2 else 0, W, 8): d.point((x, y), 1)
    d.rectangle((6, 14, 37, 37), fill=0, outline=1); d.line((22, 14, 22, 37), 1); d.line((6, 26, 37, 26), 1)
    d.line((4, 40, 39, 40), 1); d.ellipse((9, 17, 15, 23), fill=1)
    d.rectangle((92, 8, 125, 21), fill=0); d.line((92, 20, 123, 20), 1); d.rectangle((96, 10, 107, 19), outline=1)
    d.line((0, 53, W, 53), 1); d.line((0, 56, W, 56), 1)
    for x in range(6, W, 14): d.line((x, 57, x-5, 63), 1)
    d.rectangle((116, 34, 121, 55), fill=1); d.rectangle((110, 32, 127, 34), fill=1)

def hud(d, vals=(4, 3, 4, 2), coins=128):
    d.rectangle((0, 0, W, 9), fill=0)
    icons = ['f', 'd', 'h', 'b']
    for i, lv in enumerate(vals):
        x = 1 + i*24
        if icons[i] == 'f': d.rounded_rectangle((x, 3, x+4, 6), 1, fill=1); d.polygon([(x+4, 4), (x+7, 1), (x+7, 7)], fill=1)
        if icons[i] == 'd': d.ellipse((x+1, 2, x+5, 7), fill=1); d.polygon([(x+1, 4), (x+5, 4), (x+3, 0)], fill=1)
        if icons[i] == 'h': d.ellipse((x, 1, x+4, 5), fill=1); d.ellipse((x+3, 1, x+7, 5), fill=1); d.polygon([(x, 4), (x+7, 4), (x+3, 8)], fill=1)
        if icons[i] == 'b': d.polygon([(x+4, 1), (x+1, 5), (x+4, 5)], fill=1); d.polygon([(x+3, 4), (x+6, 4), (x+2, 8)], fill=1)
        for k in range(4):
            px = x+10+k*4
            if k < lv: d.rectangle((px, 3, px+2, 5), fill=1)
            else: d.point((px+1, 4), 1)
    txt = str(coins); tw = len(txt)*6; x = W-tw-10
    d.ellipse((x-3, 1, x+3, 7), fill=1); d.line((x, 2, x, 6), 0)
    d.text((x+6, -1), txt, fill=1)
    d.line((0, 10, W, 10), 1)

def nico(img, pose, cx, eye='sleepy'):
    (spr, mask), anchor = G.FRONT[pose]
    spr = spr.copy()
    if anchor: G.eyes(spr, (anchor[0], anchor[1]), anchor[2], eye)
    return blit(img, spr, mask, cx-G.W//2, 58-G.GND)

def bubble(d, x, y, t):
    w = len(t)*6+7
    d.rounded_rectangle((x, y, x+w, y+11), 3, fill=0, outline=1); d.text((x+4, y), t, fill=1)

def home():
    im = canvas(); d = ImageDraw.Draw(im); room(d)
    im = nico(im, 'SIT1', 66, 'sleepy'); d = ImageDraw.Draw(im); hud(d); bubble(d, 74, 14, 'miau?')
    return im

def home_happy():
    im = canvas(); d = ImageDraw.Draw(im); room(d)
    im = nico(im, 'WALK2', 50, 'sleepy'); d = ImageDraw.Draw(im); hud(d, (2, 4, 3, 4), 57)
    return im

def menu():
    im = canvas(); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 12), fill=1)
    d.polygon([(3, 12), (6, 4), (9, 12)], fill=0); d.polygon([(10, 12), (13, 4), (16, 12)], fill=0)
    d.text((20, 0), 'NicoOS', fill=0)
    items = ['Cuidar', 'Loja', 'Brincar', 'Ferramentas']
    for i, t in enumerate(items):
        y = 15+i*12
        if i == 2: d.rounded_rectangle((2, y-1, W-3, y+10), 3, fill=1)
        d.text((18, y-1), t, fill=0 if i == 2 else 1)
        c = 0 if i == 2 else 1
        d.rectangle((5, y+2, 11, y+7), outline=c)
    return im

def seg7(d, x, y, n, w=14, h=26, th=3):
    S = [0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F]; m = S[n]; hh = h//2
    if m & 1: d.rectangle((x+th, y, x+w-th-1, y+th-1), fill=1)
    if m & 2: d.rectangle((x+w-th, y+th, x+w-1, y+hh-1), fill=1)
    if m & 4: d.rectangle((x+w-th, y+hh+1, x+w-1, y+h-th), fill=1)
    if m & 8: d.rectangle((x+th, y+h-th, x+w-th-1, y+h-1), fill=1)
    if m & 16: d.rectangle((x, y+hh+1, x+th-1, y+h-th), fill=1)
    if m & 32: d.rectangle((x, y+th, x+th-1, y+hh-1), fill=1)
    if m & 64: d.rectangle((x+th, y+hh-1, x+w-th-1, y+hh+1), fill=1)

def clock():
    im = canvas(); d = ImageDraw.Draw(im)
    seg7(d, 4, 8, 2); seg7(d, 22, 8, 1)
    d.rectangle((40, 15, 42, 17), fill=1); d.rectangle((40, 25, 42, 27), fill=1)
    seg7(d, 47, 8, 4); seg7(d, 65, 8, 7)
    d.rectangle((4, 39, 78, 41), outline=1); d.line((5, 40, 50, 40), 1)
    d.text((4, 46), 'sex 09 out', fill=1)
    mi, mm, ma = G.mini()
    a = np.array(im, dtype=bool)
    for yy in range(mi.shape[0]):
        for xx in range(mi.shape[1]):
            if mm[yy, xx]: a[30+yy, 100+xx] = mi[yy, xx]
    for i in (0, 1): a[30+ma[2], 100+ma[i]-1:100+ma[i]+2] = True
    im = Image.fromarray(a); d = ImageDraw.Draw(im); d.text((112, 16), 'z', fill=1)
    return im

def to_oled(im, scale=6, name='x'):
    a = np.array(im, dtype=bool)
    on = np.array([235, 248, 255], np.uint8); off = np.array([8, 10, 14], np.uint8)
    rgb = np.where(a[..., None], on, off).astype(np.uint8)
    big = np.kron(rgb, np.ones((scale, scale, 1), np.uint8))
    pad = 24
    frame = np.full((big.shape[0]+2*pad, big.shape[1]+2*pad, 3), (24, 26, 32), np.uint8)
    frame[pad:-pad, pad:-pad] = big
    out = Image.fromarray(frame)
    os.makedirs('img', exist_ok=True); out.save(f'img/screen_{name}.png'); print('img/screen_'+name+'.png')

if __name__ == '__main__':
    to_oled(home(), name='home'); to_oled(home_happy(), name='walk')
    to_oled(menu(), name='menu'); to_oled(clock(), name='clock')
