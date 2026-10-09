// NicoOS — mini-jogos. Cada jogo: begin() e step() que devolve true quando sai.
#pragma once
#include <Adafruit_SSD1306.h>
#include "config.h"
#include "input.h"
#include "sprites.h"

// ================= SNAKE =================
struct Snake {
  static const int CW = 4, COLS = OLED_W/4, ROWS = (OLED_H-10)/4; // 32 x 13
  int bx[COLS*ROWS], by[COLS*ROWS], len;
  int dx, dy, ndx, ndy, fx, fy, score, best = 0;
  bool dead; uint32_t lastMove;

  void begin() {
    len = 3; dx = 1; dy = 0; ndx = 1; ndy = 0; score = 0; dead = false;
    for (int i = 0; i < len; i++){ bx[i] = 8-i; by[i] = ROWS/2; }
    dropFood(); lastMove = millis();
  }
  void dropFood(){ fx = random(COLS); fy = random(ROWS); }

  bool step(Input &in, Adafruit_SSD1306 &g) {
    if (in.pressed[BTN_B]) return true;
    if (!dead) {
      if (in.pressed[BTN_UP]    && dy==0){ ndx=0; ndy=-1; }
      if (in.pressed[BTN_DOWN]  && dy==0){ ndx=0; ndy= 1; }
      if (in.pressed[BTN_LEFT]  && dx==0){ ndx=-1; ndy=0; }
      if (in.pressed[BTN_RIGHT] && dx==0){ ndx= 1; ndy=0; }
      int spd = max(70, 150 - score*4);
      if (millis() - lastMove > (uint32_t)spd) {
        lastMove = millis(); dx=ndx; dy=ndy;
        int nx = bx[0]+dx, ny = by[0]+dy;
        if (nx<0||nx>=COLS||ny<0||ny>=ROWS) dead = true;
        for (int i=0;i<len;i++) if (bx[i]==nx&&by[i]==ny) dead = true;
        if (!dead) {
          for (int i=len;i>0;i--){ bx[i]=bx[i-1]; by[i]=by[i-1]; }
          bx[0]=nx; by[0]=ny;
          if (nx==fx&&ny==fy){ len++; score++; if(score>best)best=score; dropFood(); }
        }
      }
    } else if (in.pressed[BTN_A]) begin();

    g.clearDisplay();
    g.setTextColor(SSD1306_WHITE); g.setTextSize(1);
    g.setCursor(0,0); g.print("SNAKE "); g.print(score);
    g.setCursor(90,0); g.print("rec:"); g.print(best);
    int oy = 10;
    g.drawRect(0, oy-1, OLED_W, OLED_H-oy+1, SSD1306_WHITE);
    for (int i=0;i<len;i++)
      g.fillRect(bx[i]*CW+1, oy+by[i]*CW, CW-1, CW-1, SSD1306_WHITE);
    if ((millis()/200)%2)  // comida piscando
      g.fillCircle(fx*CW+CW/2, oy+fy*CW+CW/2, 2, SSD1306_WHITE);
    if (dead) {
      g.fillRoundRect(18, 22, 92, 22, 4, SSD1306_BLACK);
      g.drawRoundRect(18, 22, 92, 22, 4, SSD1306_WHITE);
      g.setCursor(30, 26); g.print("GAME OVER");
      g.setCursor(24, 35); g.print("A=denovo B=sair");
    }
    g.display();
    return false;
  }
};

// ================= CATCH (Nico pega petiscos) =================
struct Catch {
  float px; int score, lives; float items_x[5], items_y[5]; bool live_[5];
  uint32_t last, spawn;
  void begin(){ px = OLED_W/2; score=0; lives=3; for(int i=0;i<5;i++)live_[i]=false; last=millis(); spawn=millis(); }

  bool step(Input &in, Adafruit_SSD1306 &g) {
    if (in.pressed[BTN_B]) return true;
    float dt = (millis()-last)/1000.0f; last=millis();
    if (lives>0) {
      if (in.down[BTN_LEFT])  px -= 90*dt;
      if (in.down[BTN_RIGHT]) px += 90*dt;
      px = constrain(px, 10, OLED_W-10);
      if (millis()-spawn > 850) { spawn=millis(); for(int i=0;i<5;i++) if(!live_[i]){ live_[i]=true; items_x[i]=random(8,OLED_W-8); items_y[i]=10; break; } }
      for (int i=0;i<5;i++) if (live_[i]) {
        items_y[i] += (40+score*2)*dt;
        if (items_y[i] > OLED_H-8 && fabs(items_x[i]-px) < 10) { live_[i]=false; score++; }
        else if (items_y[i] > OLED_H) { live_[i]=false; lives--; }
      }
    } else if (in.pressed[BTN_A]) begin();

    g.clearDisplay(); g.setTextColor(SSD1306_WHITE); g.setTextSize(1);
    g.setCursor(0,0); g.print("PEGA-PETISCO "); g.print(score);
    for (int i=0;i<lives;i++) g.fillCircle(OLED_W-6-i*7, 3, 2, SSD1306_WHITE);
    // nico (cestinha simplificada: cabeça do gato)
    g.fillCircle((int)px, OLED_H-6, 6, SSD1306_WHITE);
    g.fillTriangle((int)px-6,OLED_H-9,(int)px-3,OLED_H-14,(int)px-1,OLED_H-10,SSD1306_WHITE);
    g.fillTriangle((int)px+6,OLED_H-9,(int)px+3,OLED_H-14,(int)px+1,OLED_H-10,SSD1306_WHITE);
    g.fillCircle((int)px-2, OLED_H-7, 1, SSD1306_BLACK); g.fillCircle((int)px+2, OLED_H-7, 1, SSD1306_BLACK);
    for (int i=0;i<5;i++) if (live_[i]) { g.fillCircle((int)items_x[i],(int)items_y[i],2,SSD1306_WHITE); g.drawPixel((int)items_x[i],(int)items_y[i]-3,SSD1306_WHITE); }
    if (lives<=0) {
      g.fillRoundRect(18, 22, 92, 22, 4, SSD1306_BLACK);
      g.drawRoundRect(18, 22, 92, 22, 4, SSD1306_WHITE);
      g.setCursor(40, 26); g.print("FIM!"); g.setCursor(24, 35); g.print("A=denovo B=sair");
    }
    g.display();
    return false;
  }
};

// mini-gato procedural (para os jogos)
inline void miniCat(Adafruit_SSD1306 &g, int x, int y, int dir=1) {   // cabecinha do Nico (sprite)
  static const int8_t e[3]={MINI_EYE};
  int ox=x-9, oy=y-11;
  g.drawBitmap(ox,oy,MINI_MASK,MINI_W,MINI_H,SSD1306_BLACK);
  g.drawBitmap(ox,oy,MINI_IMG, MINI_W,MINI_H,SSD1306_WHITE);
  for (int i=0;i<2;i++){ int ex=ox+e[i], ey=oy+e[2]; g.drawFastHLine(ex-1,ey-1,3,SSD1306_WHITE); g.drawPixel(ex,ey,SSD1306_WHITE); }
}

// ================= FLAPPY NICO (versão fácil) =================
inline bool anyBtn(Input &in){ for(int i=0;i<BTN_COUNT;i++) if(in.pressed[i]&&i!=BTN_B) return true; return false; }
struct Flappy {
  float y, vy; int score, best=0; bool dead, started;
  float px[3]; int gap[3]; bool passed[3]; uint32_t last, deadAt;
  static const int GAPH=34, PW=9, SPACING=64;
  void begin(){ y=30; vy=0; score=0; dead=false; started=false;
    for(int i=0;i<3;i++){ px[i]=150+i*SPACING; gap[i]=random(20,44); passed[i]=false; } last=millis(); }
  bool step(Input &in, Adafruit_SSD1306 &g) {
    if (in.pressed[BTN_B]) return true;
    float dt=(millis()-last)/16.0f; last=millis(); if(dt>3)dt=3;
    bool tap = anyBtn(in);
    if (!dead) {
      if (!started){ y=30+sinf(millis()/250.0f)*3; if(tap){ started=true; vy=-2.0f; } }
      else {
        if (tap) vy=-2.0f;
        vy+=0.12f*dt; if(vy>2.6f)vy=2.6f; y+=vy*dt;
        if (y<6){ y=6; vy=0; }                               // teto não mata
        for (int i=0;i<3;i++){ px[i]-=1.0f*dt;
          if (!passed[i] && px[i]+PW<18){ passed[i]=true; score++; if(score>best)best=score; }
          if (px[i]<-PW){ px[i]+=3*SPACING; gap[i]=random(20,44); passed[i]=false; }
          if (px[i]<22 && px[i]+PW>14){ if (y-4<gap[i]-GAPH/2 || y+4>gap[i]+GAPH/2){ dead=true; deadAt=millis(); } } }
        if (y>60){ dead=true; deadAt=millis(); }
      }
    } else if (tap && millis()-deadAt>500) begin();
    g.clearDisplay(); g.setTextColor(SSD1306_WHITE); g.setTextSize(1);
    for (int i=0;i<3;i++){ int x=(int)px[i], gt=gap[i]-GAPH/2, gb=gap[i]+GAPH/2;   // arranhadores
      g.drawRect(x,0,PW,gt,SSD1306_WHITE); g.drawRect(x,gb,PW,64-gb,SSD1306_WHITE);
      g.fillRect(x-2,gt-3,PW+4,3,SSD1306_WHITE); g.fillRect(x-2,gb,PW+4,3,SSD1306_WHITE);
      for (int yy=4;yy<gt-4;yy+=4) g.drawFastHLine(x+2,yy,PW-4,SSD1306_WHITE);
      for (int yy=gb+6;yy<62;yy+=4) g.drawFastHLine(x+2,yy,PW-4,SSD1306_WHITE); }
    for (int i=0;i<4;i++){ int cx=(int)(((millis()/40)+i*40)%170)-20; g.drawPixel(127-cx,10+i*12,SSD1306_WHITE); } // vento
    miniCat(g,18,(int)y,1);
    g.setCursor(60,2); g.print(score);
    if (!started && !dead){ g.fillRoundRect(34,46,62,13,3,SSD1306_BLACK); g.drawRoundRect(34,46,62,13,3,SSD1306_WHITE); g.setCursor(38,49); g.print("aperte algo"); }
    if (dead){ g.fillRoundRect(22,18,84,28,4,SSD1306_BLACK); g.drawRoundRect(22,18,84,28,4,SSD1306_WHITE);
      g.setCursor(40,22); g.print("ops! "); g.print(score); g.setCursor(28,34); g.print("botao=denovo B=sai"); }
    g.display(); return false;
  }
};

// ================= NICO KART =================
struct Kart {
  float lanePos; int lane, lives, fish, best=0; float dist, speed;
  struct Obj { float y; int lane; uint8_t kind; bool on; } obj[6];   // kind 0=cone 1=caixa 2=peixe
  uint32_t last, lastSpawn, hitAt; float stripe;
  static int laneX(int l){ return 40+l*24; }
  int score(){ return (int)(dist/40)+fish*3; }
  void begin(){ lane=1; lanePos=1; lives=3; fish=0; dist=0; speed=1.2f; stripe=0; hitAt=0;
    for(auto &o:obj) o.on=false; last=lastSpawn=millis(); }
  void spawn(){ for(auto &o:obj) if(!o.on){ o.on=true; o.y=-10; o.lane=random(3); o.kind=random(10)<3?2:random(2); return; } }
  void car(Adafruit_SSD1306 &g,int cx,int y,bool blink){
    if (blink) return;
    g.fillRoundRect(cx-7,y,15,16,4,SSD1306_BLACK); g.drawRoundRect(cx-7,y,15,16,4,SSD1306_WHITE);
    g.fillTriangle(cx-5,y+3,cx-4,y-3,cx-1,y+2,SSD1306_WHITE); g.fillTriangle(cx+5,y+3,cx+4,y-3,cx+1,y+2,SSD1306_WHITE); // orelhas
    g.drawRect(cx-4,y+3,9,4,SSD1306_WHITE);                                           // para-brisa
    g.drawFastHLine(cx-2,y+5,2,SSD1306_WHITE); g.drawFastHLine(cx+1,y+5,2,SSD1306_WHITE); // olhinhos
    g.fillRect(cx-9,y+3,2,4,SSD1306_WHITE); g.fillRect(cx+8,y+3,2,4,SSD1306_WHITE);   // rodas
    g.fillRect(cx-9,y+10,2,4,SSD1306_WHITE); g.fillRect(cx+8,y+10,2,4,SSD1306_WHITE);
    g.drawLine(cx-1,y+16,cx-3,y+19,SSD1306_WHITE);                                    // rabo pra fora
  }
  bool step(Input &in, Adafruit_SSD1306 &g) {
    if (in.pressed[BTN_B]) return true;
    float dt=(millis()-last)/16.0f; last=millis(); if(dt>3)dt=3;
    if (lives>0) {
      if (in.pressed[BTN_LEFT]  && lane>0) lane--;
      if (in.pressed[BTN_RIGHT] && lane<2) lane++;
      lanePos += (lane-lanePos)*0.35f;
      speed = min(3.2f, 1.2f + dist/3000.0f);
      if (in.down[BTN_A]||in.down[BTN_UP]) speed*=1.35f;                       // turbo
      dist += speed*dt; stripe=fmodf(stripe+speed*dt,12);
      if (millis()-lastSpawn > (uint32_t)max(380.0f, 1100-dist/6)) { spawn(); lastSpawn=millis(); }
      for (auto &o:obj) if (o.on){ o.y+=speed*dt;
        if (o.y>70) o.on=false;
        else if (o.lane==lane && o.y>40 && o.y<60) {
          o.on=false;
          if (o.kind==2) fish++;
          else if (millis()-hitAt>900){ lives--; hitAt=millis(); }
        } }
      if (score()>best) best=score();
    } else if (anyBtn(in)) begin();
    g.clearDisplay(); g.setTextColor(SSD1306_WHITE); g.setTextSize(1);
    g.drawFastVLine(26,0,64,SSD1306_WHITE); g.drawFastVLine(102,0,64,SSD1306_WHITE);
    for (int l=0;l<2;l++) for (int yy=-12+(int)stripe; yy<64; yy+=12) g.drawFastVLine(52+l*24,yy,6,SSD1306_WHITE);
    for (int i=0;i<4;i++){ int yy=(int)(fmodf(stripe*1.0f+i*16,64)); g.drawCircle(12,yy,3,SSD1306_WHITE); g.drawCircle(116,(yy+30)%64,3,SSD1306_WHITE); } // arbustos
    for (auto &o:obj) if (o.on){ int x=laneX(o.lane), y=(int)o.y;
      if (o.kind==0){ g.fillTriangle(x-4,y+6,x+4,y+6,x,y-4,SSD1306_WHITE); g.drawFastHLine(x-2,y+1,5,SSD1306_BLACK); }
      else if (o.kind==1){ g.drawRect(x-5,y-4,11,10,SSD1306_WHITE); g.drawLine(x-5,y-4,x+5,y+5,SSD1306_WHITE); }
      else { g.fillRoundRect(x-5,y-2,8,5,2,SSD1306_WHITE); g.fillTriangle(x+2,y,x+6,y-3,x+6,y+3,SSD1306_WHITE); g.drawPixel(x-3,y-1,SSD1306_BLACK); } }
    bool blink = (millis()-hitAt<900) && ((millis()/80)%2);
    car(g,(int)(40+lanePos*24),44,blink);
    g.setCursor(0,0); g.print(score());
    for (int i=0;i<lives;i++){ int hx=108+i*7; g.fillCircle(hx,2,1,SSD1306_WHITE); g.fillCircle(hx+2,2,1,SSD1306_WHITE); g.fillTriangle(hx-1,3,hx+3,3,hx+1,5,SSD1306_WHITE); }
    if (lives<=0){ g.fillRoundRect(22,18,84,28,4,SSD1306_BLACK); g.drawRoundRect(22,18,84,28,4,SSD1306_WHITE);
      g.setCursor(34,22); g.print("bateu! "); g.print(score()); g.setCursor(28,34); g.print("botao=denovo B=sai"); }
    g.display(); return false;
  }
};

// ================= PULO NO ARRANHADOR (doodle-jump) =================
struct ScratchJump {
  float cx, cy, vy; int score, best=0; bool dead;
  float plx[6], ply[6];
  void begin(){ cx=64; cy=40; vy=-3; score=0; dead=false;
    for(int i=0;i<6;i++){ plx[i]=random(6,104); ply[i]=54-i*11; } }
  bool step(Input &in, Adafruit_SSD1306 &g) {
    if (in.pressed[BTN_B]) return true;
    if (!dead) {
      if (in.down[BTN_LEFT]) cx-=2.4f; if (in.down[BTN_RIGHT]) cx+=2.4f;
      if (cx<0)cx=128; if (cx>128)cx=0;
      vy+=0.17f; cy+=vy;
      for (int i=0;i<6;i++) if (vy>0 && cy+6>=ply[i] && cy+6<=ply[i]+5 && fabs(cx-plx[i])<12){ vy=-3.4f; }
      if (cy<28){ float d=28-cy; cy=28; score+=(int)d; if(score>best)best=score; for(int i=0;i<6;i++){ ply[i]+=d; if(ply[i]>64){ ply[i]-=66; plx[i]=random(6,104);} } }
      if (cy>66) dead=true;
    } else if (in.pressed[BTN_A]) begin();
    g.clearDisplay(); g.setTextColor(SSD1306_WHITE); g.setTextSize(1);
    for (int i=0;i<6;i++){ int x=(int)plx[i], y=(int)ply[i];
      g.fillRect(x-11,y,22,3,SSD1306_WHITE); g.drawFastVLine(x,y-4,4,SSD1306_WHITE); g.drawFastVLine(x-3,y-2,2,SSD1306_WHITE); g.drawFastVLine(x+3,y-2,2,SSD1306_WHITE); }
    miniCat(g,(int)cx,(int)cy, vy<0?1:-1);
    g.setCursor(0,0); g.print(score/10);
    if (dead){ g.fillRoundRect(18,22,92,22,4,SSD1306_BLACK); g.drawRoundRect(18,22,92,22,4,SSD1306_WHITE);
      g.setCursor(34,26); g.print("CAIU!"); g.setCursor(24,35); g.print("A=denovo B=sair"); }
    g.display(); return false;
  }
  int points(){ return score/10; }
};
