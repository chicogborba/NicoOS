// NicoOS — interface: quarto, HUD, menu animado, toast
#pragma once
#include <Adafruit_SSD1306.h>
#include "config.h"
#include "input.h"

namespace ui {

// ---------------- bateria ----------------
inline float batteryPct() {
#if PIN_BAT_ADC >= 0
  uint32_t mv = analogReadMilliVolts(PIN_BAT_ADC);
  float v = (mv/1000.0f)*BAT_DIV;
  float p = (v-BAT_EMPTY)/(BAT_FULL-BAT_EMPTY)*100.0f;
  return p<0?0:(p>100?100:p);
#else
  return -1;
#endif
}
inline void drawBattery(Adafruit_SSD1306 &g, int x, int y) {
  float p = batteryPct();
  g.drawRect(x,y,12,6,SSD1306_WHITE); g.drawFastVLine(x+12,y+2,2,SSD1306_WHITE);
  if (p<0){ g.drawLine(x+7,y+1,x+4,y+3,SSD1306_WHITE); g.drawLine(x+4,y+3,x+6,y+3,SSD1306_WHITE); g.drawLine(x+6,y+3,x+4,y+5,SSD1306_WHITE); }
  else { int w=(int)(p/100.0f*8); g.fillRect(x+2,y+2,w,2,SSD1306_WHITE); }
}

// ---------------- ícones 7x7 ----------------
inline void icon(Adafruit_SSD1306 &g, int x, int y, char k, uint16_t c=SSD1306_WHITE) {
  uint16_t b = (c==SSD1306_WHITE)?SSD1306_BLACK:SSD1306_WHITE;
  switch (k) {
    case 'f': g.fillRoundRect(x,y+2,5,4,2,c); g.fillTriangle(x+4,y+4,x+7,y+1,x+7,y+6,c); g.drawPixel(x+1,y+3,b); break; // peixe
    case 'd': g.fillCircle(x+3,y+4,2,c); g.fillTriangle(x+1,y+3,x+5,y+3,x+3,y,c); break;          // gota
    case 'h': g.fillCircle(x+2,y+2,2,c); g.fillCircle(x+5,y+2,2,c); g.fillTriangle(x,y+3,x+7,y+3,x+3,y+7,c); break; // coração
    case 'b': g.fillTriangle(x+4,y,x+1,y+4,x+4,y+4,c); g.fillTriangle(x+3,y+3,x+6,y+3,x+2,y+7,c); break;   // raio
    case 'p': g.fillCircle(x+3,y+5,2,c); g.fillCircle(x+1,y+2,1,c); g.fillCircle(x+3,y+1,1,c); g.fillCircle(x+5,y+2,1,c); break; // pata
    case 's': g.fillRect(x,y+3,7,5,c); g.drawRect(x+2,y,3,4,c); break;                             // sacola
    case 'g': g.fillRoundRect(x,y+2,8,5,2,c); g.drawFastHLine(x+1,y+4,3,b); g.drawFastVLine(x+2,y+3,3,b); g.drawPixel(x+5,y+3,b); g.drawPixel(x+6,y+5,b); break; // controle
    case 't': g.drawLine(x,y+7,x+5,y+2,c); g.drawLine(x+1,y+7,x+6,y+2,c); g.drawCircle(x+5,y+2,2,c); break; // ferramenta
    case 'z': g.fillCircle(x+3,y+3,3,c); g.fillCircle(x+5,y+2,3,b); break;                         // lua
    case 'i': g.fillRect(x,y+4,2,3,c); g.fillRect(x+3,y+2,2,5,c); g.fillRect(x+6,y,2,7,c); break;   // barras
    case 'o': g.fillCircle(x+3,y+3,3,c); g.fillCircle(x+3,y+3,1,b); g.drawPixel(x+3,y-1,c); g.drawPixel(x+3,y+7,c); g.drawPixel(x-1,y+3,c); g.drawPixel(x+7,y+3,c); break; // engrenagem
    case 'w': g.drawCircle(x+3,y+7,6,c); g.drawCircle(x+3,y+7,3,c); g.fillRect(x-4,y+7,16,8,b); g.fillCircle(x+3,y+6,1,c); break; // wifi
    case 'q': g.drawRect(x,y,3,3,c); g.drawRect(x+5,y,3,3,c); g.drawRect(x,y+5,3,3,c); g.drawPixel(x+5,y+5,c); g.drawPixel(x+7,y+7,c); break; // qr
    case 'k': g.fillCircle(x+2,y+4,2,c); g.fillCircle(x+5,y+3,3,c); g.fillRect(x+1,y+5,7,2,c); break; // nuvem
    case 'x': g.drawLine(x,y+3,x+6,y+3,c); g.drawLine(x,y+3,x+3,y,c); g.drawLine(x,y+3,x+3,y+6,c); break; // voltar
    case 'c': g.fillCircle(x+3,y+3,3,c); g.drawFastVLine(x+3,y+1,5,b); break;                      // moeda
    case 'r': g.drawRect(x,y+1,7,6,c); g.fillRect(x+2,y+3,3,2,c); break;                            // reset
    case 'l': g.drawCircle(x+3,y+3,3,c); g.drawFastVLine(x+3,y+1,3,c); g.drawFastHLine(x+3,y+3,2,c); break; // relógio
    case 'n': g.fillTriangle(x+1,y+1,x+3,y,x+3,y+3,c); g.fillTriangle(x+6,y+1,x+4,y,x+4,y+3,c); g.fillCircle(x+3,y+4,3,c); break; // gatinho
  }
}

// ---------------- moeda ----------------
inline void coinIcon(Adafruit_SSD1306 &g, int x, int y) {
  g.fillCircle(x,y,3,SSD1306_WHITE); g.drawPixel(x,y,SSD1306_BLACK); g.drawFastVLine(x,y-1,3,SSD1306_BLACK);
}
inline void coinHUD(Adafruit_SSD1306 &g, uint32_t coins) {
  char b[8]; snprintf(b,8,"%lu",(unsigned long)coins);
  int w = strlen(b)*6;
  int x = OLED_W - w - 10;
  coinIcon(g,x,3); g.setTextColor(SSD1306_WHITE); g.setTextSize(1); g.setCursor(x+6,0); g.print(b);
}

// ---------------- quarto detalhado ----------------
inline void room(Adafruit_SSD1306 &g, uint32_t t, bool night) {
  // papel de parede (bolinhas) e rodapé
  for (int yy=4; yy<52; yy+=8) for (int xx=(yy/8)%2?4:0; xx<OLED_W; xx+=8) g.drawPixel(xx,yy,SSD1306_WHITE);
  g.fillRect(6,14,32,24,SSD1306_BLACK); g.fillRect(92,8,34,14,SSD1306_BLACK);  // limpa atrás da janela/prateleira
  g.drawFastHLine(0,53,OLED_W,SSD1306_WHITE);
  // chão + rodapé + tábuas
  g.drawFastHLine(0,56,OLED_W,SSD1306_WHITE);
  for (int x=6;x<OLED_W;x+=14) g.drawLine(x,57,x-5,63,SSD1306_WHITE);
  // janela (esquerda)
  g.drawRect(6,14,32,24,SSD1306_WHITE); g.drawFastVLine(22,14,24,SSD1306_WHITE); g.drawFastHLine(6,26,32,SSD1306_WHITE);
  g.drawFastHLine(4,40,36,SSD1306_WHITE);                 // peitoril
  if (night){ g.fillCircle(31,21,4,SSD1306_WHITE); g.fillCircle(33,20,4,SSD1306_BLACK);
    for (int i=0;i<5;i++){int sx=9+i*5,sy=18+(i%2)*7; if((t/500+i)%3)g.drawPixel(sx,sy,SSD1306_WHITE);} }
  else { g.fillCircle(12,20,3,SSD1306_WHITE);             // sol
    int cxp=20+((t/80)%34); if(cxp<36){g.fillCircle(cxp,22,2,SSD1306_WHITE);g.fillCircle(cxp+3,22,2,SSD1306_WHITE);g.fillCircle(cxp+2,20,2,SSD1306_WHITE);} } // nuvem passando
  // prateleira + porta-retrato (direita em cima)
  g.drawFastHLine(92,20,32,SSD1306_WHITE);
  g.drawRect(96,10,12,10,SSD1306_WHITE); g.fillCircle(100,15,1,SSD1306_WHITE); g.fillCircle(103,15,1,SSD1306_WHITE); g.drawPixel(101,17,SSD1306_WHITE); g.drawPixel(102,17,SSD1306_WHITE);
  g.fillRect(113,15,4,5,SSD1306_WHITE);                   // livrinho
  // caminha do gato (esquerda no chão)
  g.drawRoundRect(2,48,26,8,3,SSD1306_WHITE); g.drawFastHLine(4,51,22,SSD1306_WHITE);
  // arranhador (direita no chão)
  g.fillRect(116,34,6,22,SSD1306_WHITE); g.fillRect(110,32,18,3,SSD1306_WHITE);
  for (int i=0;i<4;i++) g.drawFastHLine(116,37+i*4,6,SSD1306_BLACK);  // ranhuras
  g.drawLine(119,34,124,30,SSD1306_WHITE); g.fillCircle(125,29,2,SSD1306_WHITE); // bolinha pendurada
  // tapete central
  g.drawFastHLine(46,56,38,SSD1306_WHITE); g.drawFastHLine(49,57,32,SSD1306_WHITE); g.drawFastHLine(52,58,26,SSD1306_WHITE);
  // vasinho
  g.fillRect(40,50,6,6,SSD1306_WHITE); g.drawLine(43,50,43,45,SSD1306_WHITE); g.drawLine(43,47,40,43,SSD1306_WHITE); g.drawLine(43,47,46,43,SSD1306_WHITE);
}

// mini status com ícones (canto superior esquerdo)
inline void miniBar(Adafruit_SSD1306 &g, int x, int y, float v) {
  g.drawRect(x,y,16,4,SSD1306_WHITE);
  int w=(int)(v/100.0f*14); g.fillRect(x+1,y+1,w,2,SSD1306_WHITE);
  if (v<25 && (millis()/300)%2) g.fillRect(x+1,y+1,14,2,SSD1306_BLACK);
}

// ---------------- toast ----------------
struct Toast {
  char msg[24]=""; uint32_t until=0; uint32_t born=0;
  void show(const char* m, uint32_t ms=1200){ strncpy(msg,m,23); born=millis(); until=millis()+ms; }
  void draw(Adafruit_SSD1306 &g){
    if (millis()>until) return;
    int w=strlen(msg)*6+12, x=(OLED_W-w)/2;
    int age=millis()-born; int y = age<160 ? 46-(age/160.0f)*22 : 24;  // sobe ao aparecer
    g.fillRoundRect(x,y,w,15,5,SSD1306_BLACK); g.drawRoundRect(x,y,w,15,5,SSD1306_WHITE);
    g.setTextColor(SSD1306_WHITE); g.setTextSize(1); g.setCursor(x+6,y+4); g.print(msg);
  }
};

// ---------------- header ----------------
inline void header(Adafruit_SSD1306 &g, const char* title) {
  g.fillRect(0,0,OLED_W,13,SSD1306_WHITE);
  g.fillTriangle(3,12,6,4,9,12,SSD1306_BLACK); g.fillTriangle(10,12,13,4,16,12,SSD1306_BLACK);   // orelhinhas
  g.fillTriangle(4,12,6,7,8,12,SSD1306_WHITE); g.fillTriangle(11,12,13,7,15,12,SSD1306_WHITE);
  g.setTextColor(SSD1306_BLACK); g.setTextSize(1); g.setCursor(20,3); g.print(title);
}

// ---------------- menu animado ----------------
struct Menu {
  int sel=0, top=0; float hy=16; uint32_t openAt=0;
  void open(){ sel=0; top=0; hy=-14; openAt=millis(); }
  void nav(Input &in, int n){
    if (in.pressed[BTN_UP])   sel=(sel-1+n)%n;
    if (in.pressed[BTN_DOWN]) sel=(sel+1)%n;
    if (sel<top) top=sel; if (sel>top+3) top=sel-3;
  }
  // items: textos. subs: segunda linha opcional (preços etc) ou nullptr
  void draw(Adafruit_SSD1306 &g, const char* title, const char* const* items, int n,
            const char* const* subs=nullptr, const char* icons=nullptr) {
    g.clearDisplay();
    header(g, title);
    const int rows=4, rh=12, y0=15;
    int tY = y0 + (sel-top)*rh - 1;
    hy += (tY-hy)*0.4f;                       // highlight desliza suave
    g.fillRoundRect(2,(int)hy,OLED_W-4,rh,3,SSD1306_WHITE);
    for (int i=0;i<rows && top+i<n;i++){
      int idx=top+i, y=y0+i*rh;
      int slide = max(0, 44 - (int)((millis()-openAt)/3) - i*6); // entra da direita
      bool seld=(idx==sel);
      g.setTextColor(seld?SSD1306_BLACK:SSD1306_WHITE); g.setTextSize(1);
      int tx = 10;
      if (icons && icons[idx]) { icon(g, 5+slide, y+2, icons[idx], seld?SSD1306_BLACK:SSD1306_WHITE); tx = 17; }
      if (seld) tx += (int)(sinf(millis()/180.0f)*1.0f+1);   // item ativo "respira"
      g.setCursor(tx+slide, y+2); g.print(items[idx]);
      if (subs && subs[idx]){ int sx=OLED_W-6-strlen(subs[idx])*6; g.setCursor(sx-slide, y+2); g.print(subs[idx]); }
    }
    if (n>rows){ int th=(OLED_H-15)*rows/n; int ty=15+(OLED_H-15-th)*top/(n-rows); g.fillRoundRect(OLED_W-2,ty,2,th,1,SSD1306_WHITE); }
  }
};

} // namespace ui
