// NicoOS — o gato Nico: status, moedas, comportamento e sprites pixel-art
#pragma once
#include <Adafruit_SSD1306.h>
#include <Preferences.h>
#include "config.h"
#include "sprites.h"

enum Act { A_SIT, A_WALK, A_LOAF, A_SLEEP, A_EAT, A_BATH, A_HAPPY, A_GROOM, A_PLAY, A_STRETCH };

struct Nico {
  float hunger=80, hygiene=80, happy=80, energy=80;
  uint32_t age=0, coins=25; float ageAccum=0;
  Preferences prefs;

  float x=64; int dir=1; Act act=A_SIT; float targetX=64;
  uint32_t actUntil=0, nextBrain=0, lastTick=0, lookUntil=0;
  uint32_t reactUntil=0; char emote=0;
  const char* sayTxt=nullptr; uint32_t sayUntil=0;      // 'h' coração, 'm' música, '!' '?'

  void begin() {
    prefs.begin("nico", false);
    hunger=prefs.getFloat("hu",80); hygiene=prefs.getFloat("hy",80);
    happy=prefs.getFloat("ha",80);  energy=prefs.getFloat("en",80);
    age=prefs.getUInt("age",0); coins=prefs.getUInt("coin",25); lastTick=millis();
  }
  void save() {
    prefs.putFloat("hu",hunger); prefs.putFloat("hy",hygiene); prefs.putFloat("ha",happy);
    prefs.putFloat("en",energy); prefs.putUInt("age",age); prefs.putUInt("coin",coins);
  }
  void reset(){ hunger=hygiene=happy=energy=95; age=0; coins=25; x=64; act=A_SIT; save(); }
  static float cl(float v){ return v<0?0:(v>100?100:v); }

  void addCoins(int n){ coins+=n; if(coins>9999)coins=9999; }
  bool spend(int n){ if(coins<(uint32_t)n) return false; coins-=n; return true; }
  void react(char e,uint32_t ms=1300){ emote=e; reactUntil=millis()+ms; }

  void say(const char* t, uint32_t ms=1500){ sayTxt=t; sayUntil=millis()+ms; }

  // ---- ações comandadas pelas setas na tela inicial ----
  void cmdWalk(int d){                       // ◄ ►: anda pra um lado
    if (act==A_SLEEP) { wake(); return; }
    targetX = constrain(x + d*34, 18.0f, 110.0f); dir=d; act=A_WALK; nextBrain=millis()+4000;
  }
  void cmdPet(){                             // ▲: carinho, ele pula feliz
    if (act==A_SLEEP) { wake(); return; }
    happy=cl(happy+3); act=A_HAPPY; actUntil=millis()+1300; react('h',1400);
    static const char* L[]={"purr","miau!",":3","hehe"}; say(L[random(4)],1100);
  }
  void cmdLie(){                             // ▼: deita; de novo: dorme
    if (act==A_LOAF){ act=A_SLEEP; say("boa noite",1200); return; }
    if (act==A_SLEEP) return;
    act=A_LOAF; actUntil=millis()+9000; nextBrain=millis()+9000;
  }
  void cmdCall(){                            // B: chama ele, ele olha
    if (act==A_SLEEP){ wake(); say("hm?",1000); return; }
    if (act==A_WALK){ act=A_SIT; actUntil=millis()+1500; }
    lookUntil=millis()+1400;
    static const char* L[]={"miau?","oi","que foi","hm?"}; say(L[random(4)],1200);
  }

  // botão apertado na home: ele te olha (ou acorda)
  void poke(){
    if (act==A_SLEEP){ act=A_STRETCH; actUntil=millis()+1100; nextBrain=millis()+1500; react('!',900); return; }
    if (act==A_WALK){ act=A_SIT; actUntil=millis()+1500; }
    lookUntil=millis()+1200;
  }

  void update() {
    uint32_t now=millis(); float dt=(now-lastTick)/60000.0f; lastTick=now;
    if (dt>0) {
      hunger =cl(hunger -2.0f*dt); hygiene=cl(hygiene-1.2f*dt); happy=cl(happy-1.6f*dt);
      energy = (act==A_SLEEP)? cl(energy+8.0f*dt) : cl(energy-0.9f*dt);
      ageAccum+=dt; if(ageAccum>=1){uint32_t w=(uint32_t)ageAccum; age+=w; ageAccum-=w;}
    }
    brain(now); anim(now);
  }

  void brain(uint32_t now) {
    if (act==A_EAT||act==A_BATH||act==A_HAPPY||act==A_STRETCH) {
      if (now>actUntil){ act=A_SIT; actUntil=now+800; nextBrain=now+900; } return;
    }
    if (energy<20 && act!=A_SLEEP) { act=A_SLEEP; return; }
    if (act==A_SLEEP) { if(energy>62){ act=A_STRETCH; actUntil=now+1100; } return; }
    if (act==A_WALK || now<nextBrain || now<actUntil) return;
    int r=random(100);
    // humor muda o que ele prefere fazer
    int walkP = happy>50 ? 38 : 20;
    if (r<walkP)      { targetX=random(18,108); dir=targetX>x?1:-1; act=A_WALK; }
    else if (r<walkP+18){ act=A_LOAF;  actUntil=now+random(3000,7000); }
    else if (r<walkP+32){ act=A_GROOM; actUntil=now+random(1600,3000); }
    else if (r<walkP+44 && happy>40){ act=A_PLAY; actUntil=now+random(2000,3500); react('m',2400); }
    else if (r<walkP+50){ act=A_STRETCH; actUntil=now+1200; }
    else              { act=A_SIT; actUntil=now+random(1500,3500); if(happy>70&&random(3)==0) react('h',1200); }
    nextBrain=now+random(1500,3500);
  }

  void anim(uint32_t now) {
    if (act==A_WALK) {
      if (x<targetX-1){ x+=0.55f; dir=1; } else if (x>targetX+1){ x-=0.55f; dir=-1; }
      else { act=A_SIT; actUntil=now+900; nextBrain=now+900; }
      x=constrain(x,18.0f,110.0f);
    }
  }

  void doEat(int a){ hunger=cl(hunger+a); act=A_EAT; actUntil=millis()+2200; happy=cl(happy+4); react('h',1600); }
  void doBath(){ hygiene=cl(hygiene+45); act=A_BATH; actUntil=millis()+2400; }
  void doPlayJoy(int a){ happy=cl(happy+a); energy=cl(energy-5); act=A_HAPPY; actUntil=millis()+1700; react('h',1700); }
  void doSleep(){ act=A_SLEEP; }
  void wake(){ if(act==A_SLEEP){ act=A_STRETCH; actUntil=millis()+1100; nextBrain=millis()+1500; } }
  float worst(){ float w=hunger; w=min(w,hygiene); w=min(w,happy); w=min(w,energy); return w; }
  bool happyFace(){ return worst()>62; }

  // ---- olhos desenhados por cima do sprite (mesma lógica do gerador) ----
  enum Eye { E_SLEEPY, E_OPEN, E_WIDE, E_CLOSED, E_HAPPY };
  static void drawEyes(Adafruit_SSD1306 &g, int ox, int oy, const int8_t a[3], bool mir, Eye k, int sw=NICO_W) {
    if (a[0]<0) return;
    for (int i=0;i<2;i++){
      int x = ox + (mir ? (sw-1-a[i]) : a[i]), y = oy + a[2];
      g.fillRect(x-3,y-2,7,5,SSD1306_BLACK);
      switch(k){
        case E_SLEEPY: g.drawFastHLine(x-2,y-1,5,SSD1306_WHITE); g.drawFastHLine(x-1,y,3,SSD1306_WHITE); break;
        case E_OPEN:   g.fillRect(x-1,y-1,3,3,SSD1306_WHITE); g.drawPixel(x-1,y-1,SSD1306_BLACK); break;
        case E_WIDE:   g.fillRect(x-2,y-2,4,4,SSD1306_WHITE); g.drawPixel(x-2,y-2,SSD1306_BLACK); break;
        case E_CLOSED: g.drawFastHLine(x-2,y,5,SSD1306_WHITE); break;
        case E_HAPPY:  g.drawPixel(x-2,y+1,SSD1306_WHITE); g.drawPixel(x-1,y,SSD1306_WHITE); g.drawPixel(x,y-1,SSD1306_WHITE);
                       g.drawPixel(x+1,y,SSD1306_WHITE); g.drawPixel(x+2,y+1,SSD1306_WHITE); break;
      }
    }
  }

  struct Pose { const uint8_t *r,*rm,*l,*lm; const int8_t* eye; };
  #define POSE(n) static const int8_t EY_##n[3]={NICO_##n##_EYE}; static const Pose P_##n={NICO_##n##_R,NICO_##n##_RM,NICO_##n##_L,NICO_##n##_LM,EY_##n};
  const Pose& pose(uint32_t t, Eye &eye) {
    POSE(SIT1) POSE(SIT2) POSE(SIT3) POSE(GROOM) POSE(LOAF) POSE(EAT1) POSE(EAT2)
    POSE(WALK1) POSE(WALK2) POSE(WALK3) POSE(WALK4) POSE(STRETCH) POSE(SLEEP1) POSE(SLEEP2)
    bool blink=(t%4300)<150;
    int tail=(t/700)%4; const Pose& sitp = tail==1?P_SIT2:(tail==3?P_SIT3:P_SIT1);
    eye = blink?E_CLOSED:E_SLEEPY;
    switch (act) {
      case A_WALK:   { int f=(t/110)%4; return f==0?P_WALK1:f==1?P_WALK2:f==2?P_WALK3:P_WALK4; }
      case A_EAT:    eye=E_CLOSED; return (t/260)%2?P_EAT2:P_EAT1;
      case A_SLEEP:  return (t/1000)%2?P_SLEEP2:P_SLEEP1;
      case A_LOAF:   if ((t/2600)%3==0) eye=E_CLOSED; return P_LOAF;
      case A_GROOM:  eye=E_CLOSED; return (t/400)%2?P_GROOM:P_SIT1;
      case A_STRETCH:eye=E_CLOSED; return P_STRETCH;
      case A_HAPPY:  eye=E_HAPPY; return sitp;
      case A_PLAY:   eye=blink?E_CLOSED:E_OPEN; return sitp;
      default:
        if (millis()<lookUntil) eye=E_WIDE;
        else if (!blink && happyFace() && (t/3200)%5==0) eye=E_HAPPY;
        else if (!blink && worst()<35) eye=E_OPEN;      // preocupado: olho aberto
        return sitp;
    }
  }
  #undef POSE

  void draw(Adafruit_SSD1306 &g, uint32_t t) {
    int baseY=58, cx=(int)x;
    if (act==A_BATH){ drawBath(g,cx,baseY,t); return; }
    int hop = (act==A_HAPPY) ? -(int)(fabsf(sinf(t/110.0f))*6) : 0;
    int lx=cx-NICO_W/2, ty=baseY-NICO_GND+hop;
    Eye e; const Pose& p=pose(t,e); bool mir=(dir<0);
    g.drawBitmap(lx,ty,mir?p.lm:p.rm,NICO_W,NICO_H,SSD1306_BLACK);
    g.drawBitmap(lx,ty,mir?p.l:p.r, NICO_W,NICO_H,SSD1306_WHITE);
    drawEyes(g,lx,ty,p.eye,mir,e);
    if (act==A_SLEEP) zzz(g,cx+6,ty+26,t);
    if (act==A_PLAY)  ball(g,cx+dir*22,baseY,t);
    if (millis()<sayUntil && sayTxt) bubble(g,cx,ty+2,sayTxt);
    else drawEmote(g,cx+dir*12,ty+4,t);
  }
  static void bubble(Adafruit_SSD1306 &g,int cx,int topY,const char* txt){
    int w=strlen(txt)*6+7, bx=constrain(cx-w/2,1,OLED_W-w-1), by=max(11,topY-12);
    g.fillRoundRect(bx,by,w,11,3,SSD1306_BLACK); g.drawRoundRect(bx,by,w,11,3,SSD1306_WHITE);
    g.drawLine(cx,by+10,cx-2,by+13,SSD1306_WHITE);
    g.setTextColor(SSD1306_WHITE); g.setTextSize(1); g.setCursor(bx+4,by+2); g.print(txt);
  }

  static void zzz(Adafruit_SSD1306 &g,int x,int y,uint32_t t){
    g.setTextColor(SSD1306_WHITE); g.setTextSize(1);
    for (int i=0;i<3;i++){ int ph=((t/400)+i*4)%12; if(ph<9){ g.setCursor(x+i*4+ph/3,y-ph*2-i*3); g.print("z"); } }
  }
  void ball(Adafruit_SSD1306 &g,int x,int baseY,uint32_t t){
    int b=(int)(fabsf(sinf(t/180.0f))*10);
    g.fillCircle(x,baseY-3-b,3,SSD1306_BLACK); g.drawCircle(x,baseY-3-b,3,SSD1306_WHITE);
    g.drawLine(x-2,baseY-3-b,x+2,baseY-3-b,SSD1306_WHITE);
  }

  void drawEmote(Adafruit_SSD1306 &g, int cx, int topY, uint32_t t) {
    char e=emote; if (millis()>reactUntil) {
      if (hunger<20) e='!'; else if (hygiene<18||happy<20) e='?'; else e=0;
    }
    if (!e) return;
    int yy=topY-((t/140)%3), bx=cx;
    g.fillRoundRect(bx-6,yy-6,13,11,3,SSD1306_BLACK); g.drawRoundRect(bx-6,yy-6,13,11,3,SSD1306_WHITE);
    g.drawLine(bx-1,yy+5,bx-3,yy+7,SSD1306_WHITE);              // rabinho do balão
    if (e=='h'){ g.fillCircle(bx-1,yy-2,1,SSD1306_WHITE); g.fillCircle(bx+1,yy-2,1,SSD1306_WHITE);
                 g.drawFastHLine(bx-2,yy-1,5,SSD1306_WHITE); g.drawFastHLine(bx-1,yy,3,SSD1306_WHITE); g.drawPixel(bx,yy+1,SSD1306_WHITE); }
    else if (e=='m'){ g.drawFastVLine(bx+1,yy-4,6,SSD1306_WHITE); g.drawFastHLine(bx+1,yy-4,3,SSD1306_WHITE); g.fillCircle(bx,yy+2,1,SSD1306_WHITE); }
    else { g.setTextColor(SSD1306_WHITE); g.setTextSize(1); g.setCursor(bx-2,yy-4); g.print(e); }
  }

  void drawBath(Adafruit_SSD1306 &g, int cx, int baseY, uint32_t t) {
    // Nico dentro da banheira (usa o pãozinho, só a cabeça aparece)
    int ty=baseY-NICO_GND-2;
    static const int8_t ey[3]={NICO_LOAF_EYE};
    g.drawBitmap(cx-NICO_W/2,ty,NICO_LOAF_RM,NICO_W,NICO_H,SSD1306_BLACK);
    g.drawBitmap(cx-NICO_W/2,ty,NICO_LOAF_R, NICO_W,NICO_H,SSD1306_WHITE);
    drawEyes(g,cx-NICO_W/2,ty,ey,false,E_CLOSED);
    g.fillRoundRect(cx-20,baseY-12,40,13,4,SSD1306_BLACK);
    g.drawRoundRect(cx-20,baseY-12,40,13,4,SSD1306_WHITE);
    for (int i=0;i<9;i++){ int bx=cx-18+i*4+((t/150+i)%2); g.fillCircle(bx,baseY-12,2+(i%2),SSD1306_WHITE); }  // espuma
    for (int i=0;i<5;i++){ int bx=cx-12+i*6, yy=baseY-16-((t/100+i*5)%18); g.drawCircle(bx,yy,1+(i%2),SSD1306_WHITE); }
    g.fillRect(cx-16,baseY+1,3,3,SSD1306_WHITE); g.fillRect(cx+13,baseY+1,3,3,SSD1306_WHITE);   // pezinhos da banheira
  }
};
