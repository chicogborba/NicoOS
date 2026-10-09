// NicoOS — relógio: hora do sistema, acerto manual e 3 mostradores (digital, analógico, Nico)
#pragma once
#include <time.h>
#include <sys/time.h>
#include <Preferences.h>
#include <Adafruit_SSD1306.h>
#include "config.h"
#include "sprites.h"

namespace clk {

inline bool valid(){ return time(nullptr) > 1700000000; }   // já tem hora real?

inline void beginTZ(){ setenv("TZ", NICO_TZ, 1); tzset(); }

// restaura a última hora salva (aproximada) se o relógio zerou
inline void restore(Preferences &p){
  beginTZ();
  if (!valid()){ uint32_t e=p.getUInt("epoch",0); if(e>1700000000){ timeval tv={(time_t)e,0}; settimeofday(&tv,nullptr);} }
}
inline void persist(Preferences &p){ if(valid()) p.putUInt("epoch",(uint32_t)time(nullptr)); }

inline void setLocal(Preferences &p, int h, int m){
  time_t now=time(nullptr); tm t; localtime_r(&now,&t);
  if (!valid()){ t.tm_year=2026-1900; t.tm_mon=0; t.tm_mday=1; }
  t.tm_hour=h; t.tm_min=m; t.tm_sec=0; t.tm_isdst=-1;
  timeval tv={mktime(&t),0}; settimeofday(&tv,nullptr); persist(p);
}
inline tm now(){ time_t n=time(nullptr); tm t; localtime_r(&n,&t); return t; }

static const char* DOW[]={"dom","seg","ter","qua","qui","sex","sab"};
static const char* MON[]={"jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"};

// ---- dígitos de 7 segmentos arredondados ----
inline void seg7(Adafruit_SSD1306 &g, int x, int y, int d, int w=14, int h=26, int th=3) {
  static const uint8_t S[10]={0x3F,0x06,0x5B,0x4F,0x66,0x6D,0x7D,0x07,0x7F,0x6F};
  uint8_t m=S[d%10]; int hh=h/2;
  if(m&0x01) g.fillRoundRect(x+th,y,w-2*th,th,1,SSD1306_WHITE);              // a
  if(m&0x02) g.fillRoundRect(x+w-th,y+th,th,hh-th,1,SSD1306_WHITE);          // b
  if(m&0x04) g.fillRoundRect(x+w-th,y+hh+1,th,hh-th,1,SSD1306_WHITE);        // c
  if(m&0x08) g.fillRoundRect(x+th,y+h-th,w-2*th,th,1,SSD1306_WHITE);         // d
  if(m&0x10) g.fillRoundRect(x,y+hh+1,th,hh-th,1,SSD1306_WHITE);             // e
  if(m&0x20) g.fillRoundRect(x,y+th,th,hh-th,1,SSD1306_WHITE);               // f
  if(m&0x40) g.fillRoundRect(x+th,y+hh-1,w-2*th,th,1,SSD1306_WHITE);         // g
}

inline void miniNico(Adafruit_SSD1306 &g, int x, int y, bool sleepy){
  static const int8_t e[3]={MINI_EYE};
  g.drawBitmap(x,y,MINI_MASK,MINI_W,MINI_H,SSD1306_BLACK);
  g.drawBitmap(x,y,MINI_IMG, MINI_W,MINI_H,SSD1306_WHITE);
  for(int i=0;i<2;i++){ int ex=x+e[i], ey=y+e[2];
    if (sleepy) g.drawFastHLine(ex-1,ey,3,SSD1306_WHITE);
    else { g.drawFastHLine(ex-1,ey-1,3,SSD1306_WHITE); g.drawPixel(ex,ey,SSD1306_WHITE); } }
}

// ---- DIGITAL ----
inline void drawDigital(Adafruit_SSD1306 &g, uint32_t ms) {
  tm t=now(); g.clearDisplay();
  int x=4, y=8;
  seg7(g,x,y,t.tm_hour/10); seg7(g,x+18,y,t.tm_hour%10);
  if ((ms/500)%2){ g.fillRoundRect(x+36,y+7,3,3,1,SSD1306_WHITE); g.fillRoundRect(x+36,y+17,3,3,1,SSD1306_WHITE); }
  seg7(g,x+43,y,t.tm_min/10); seg7(g,x+61,y,t.tm_min%10);
  // segundos como barrinha que enche
  g.drawRect(x,y+31,75,3,SSD1306_WHITE); g.fillRect(x+1,y+32,t.tm_sec*73/59,1,SSD1306_WHITE);
  g.setTextColor(SSD1306_WHITE); g.setTextSize(1);
  char b[24]; snprintf(b,24,"%s %02d %s",DOW[t.tm_wday],t.tm_mday,MON[t.tm_mon]);
  g.setCursor(x,y+40); g.print(b);
  if (!valid()){ g.setCursor(x,y+50); g.print("acerte a hora"); }
  // Nico cochilando do lado, com zzz
  miniNico(g,100,30,true);
  int z=(ms/600)%3; g.setCursor(112-z,22-z*4); g.print("z");
  g.display();
}

// ---- ANALÓGICO (relógio-gato: orelhas + olhos que seguem o segundo) ----
inline void drawAnalog(Adafruit_SSD1306 &g, uint32_t ms) {
  tm t=now(); g.clearDisplay();
  int cx=64, cy=34, r=27;
  g.fillTriangle(cx-24,cy-14,cx-20,cy-33,cx-8,cy-25,SSD1306_WHITE);   // orelhas
  g.fillTriangle(cx+24,cy-14,cx+20,cy-33,cx+8,cy-25,SSD1306_WHITE);
  g.fillTriangle(cx-21,cy-17,cx-19,cy-28,cx-12,cy-24,SSD1306_BLACK);
  g.fillTriangle(cx+21,cy-17,cx+19,cy-28,cx+12,cy-24,SSD1306_BLACK);
  g.fillCircle(cx,cy,r,SSD1306_BLACK); g.drawCircle(cx,cy,r,SSD1306_WHITE); g.drawCircle(cx,cy,r-1,SSD1306_WHITE);
  for (int i=0;i<12;i++){ float a=i*PI/6; int l=(i%3==0)?4:2;
    g.drawLine(cx+(r-2)*sinf(a),cy-(r-2)*cosf(a),cx+(r-2-l)*sinf(a),cy-(r-2-l)*cosf(a),SSD1306_WHITE); }
  // olhinhos que olham pros lados a cada segundo
  int look = (t.tm_sec%2)?2:-2;
  g.fillCircle(cx-8,cy-9,3,SSD1306_WHITE); g.fillCircle(cx+8,cy-9,3,SSD1306_WHITE);
  g.fillCircle(cx-8+look,cy-9,1,SSD1306_BLACK); g.fillCircle(cx+8+look,cy-9,1,SSD1306_BLACK);
  g.drawPixel(cx,cy+11,SSD1306_WHITE); // nariz
  float ah=((t.tm_hour%12)+t.tm_min/60.0f)*PI/6, am=(t.tm_min+t.tm_sec/60.0f)*PI/30, as=t.tm_sec*PI/30;
  for (int d=-1; d<=1; d++) g.drawLine(cx+d,cy,cx+d+13*sinf(ah),cy-13*cosf(ah),SSD1306_WHITE);
  g.drawLine(cx,cy,cx+20*sinf(am),cy-20*cosf(am),SSD1306_WHITE); g.drawLine(cx+1,cy,cx+1+20*sinf(am),cy-20*cosf(am),SSD1306_WHITE);
  g.drawLine(cx,cy,cx+23*sinf(as),cy-23*cosf(as),SSD1306_WHITE);
  g.fillCircle(cx,cy,2,SSD1306_WHITE);
  // rabo balançando embaixo (pêndulo do Kit-Cat)
  float sw=sinf(ms/300.0f)*0.5f; int tx=cx+10*sinf(sw), ty=cy+r+8;
  g.drawLine(cx,cy+r,tx,ty,SSD1306_WHITE); g.drawLine(cx+1,cy+r,tx+1,ty,SSD1306_WHITE);
  g.setTextColor(SSD1306_WHITE); g.setTextSize(1);
  char b[8]; snprintf(b,8,"%02d:%02d",t.tm_hour,t.tm_min); g.setCursor(0,56); g.print(b);
  snprintf(b,8,"%02d/%02d",t.tm_mday,t.tm_mon+1); g.setCursor(98,56); g.print(b);
  g.display();
}

// ---- NICO (sprite grande + hora) ----
inline void drawNicoClock(Adafruit_SSD1306 &g, uint32_t ms) {
  tm t=now(); g.clearDisplay();
  static const int8_t e[3]={NICO_LOAF_EYE};
  g.drawBitmap(-4,20,NICO_LOAF_R,NICO_W,NICO_H,SSD1306_WHITE);
  int ex[2]={-4+e[0],-4+e[1]};
  bool bl=(ms%4000)<150;
  for(int i=0;i<2;i++){ int x=ex[i], y=20+e[2]; g.fillRect(x-3,y-2,7,5,SSD1306_BLACK);
    if(bl) g.drawFastHLine(x-2,y,5,SSD1306_WHITE); else { g.drawFastHLine(x-2,y-1,5,SSD1306_WHITE); g.drawFastHLine(x-1,y,3,SSD1306_WHITE);} }
  g.setTextColor(SSD1306_WHITE); g.setTextSize(3);
  char b[8]; snprintf(b,8,"%02d",t.tm_hour); g.setCursor(50,6); g.print(b);
  snprintf(b,8,"%02d",t.tm_min); g.setCursor(50,32); g.print(b);
  if ((ms/500)%2) { g.fillRect(90,14,3,3,SSD1306_WHITE); g.fillRect(90,40,3,3,SSD1306_WHITE); }
  g.setTextSize(1); g.setCursor(98,14); g.print(DOW[t.tm_wday]);
  snprintf(b,8,"%02d",t.tm_mday); g.setCursor(98,26); g.print(b);
  g.setCursor(98,38); g.print(MON[t.tm_mon]);
  g.display();
}

inline void draw(Adafruit_SSD1306 &g, int style, uint32_t ms){
  if (style==0) drawDigital(g,ms); else if (style==1) drawAnalog(g,ms); else drawNicoClock(g,ms);
}

} // namespace clk
