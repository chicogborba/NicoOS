// ███ NicoOS ███ — tamagotchi + games + tools (gato Nico) no handheld BINI Cat
#include <Arduino.h>
#include <Wire.h>
#include <esp_sleep.h>
#include "driver/gpio.h"
#include <Adafruit_SSD1306.h>
#include <Preferences.h>
#include "config.h"
#include "input.h"
#include "nico.h"
#include "ui.h"
#include "games.h"
#include "wifitools.h"
#include "clockapp.h"

Adafruit_SSD1306 oled(OLED_W, OLED_H, &Wire, -1);
Input in; Nico nico; ui::Toast toast; ui::Menu menu;
Snake snake; Catch catchg; Flappy flappy; ScratchJump jumpg; Kart kart; WifiAP ap;
Preferences sys;

enum State { ST_BOOT, ST_HOME, ST_MENU, ST_CARE, ST_SHOP, ST_GAMES, ST_SNAKE, ST_CATCH,
             ST_FLAPPY, ST_JUMP, ST_KART, ST_TOOLS, ST_WIFI_PICK, ST_WIFI_ON, ST_QR, ST_STATUS,
             ST_SETTINGS, ST_SLEEPMENU, ST_NAP, ST_CLOCK, ST_CLOCKMENU, ST_TIMESET };
State st = ST_BOOT;
uint32_t stEnter = 0;
bool flip = true;
bool confirmReset = false;
uint32_t lastSave = 0;
uint32_t lastInput = 0, lastTimeSave = 0;
int clockStyle = 0, clockAuto = 1;            // auto: 0=off 1=30s 2=1min 3=5min
const uint16_t AUTO_S[4] = {0,30,60,300};
const char* STYLE_N[3] = {"Digital","Analogico","Nico"};
State clockReturn = ST_HOME;
int tsH=12, tsM=0, tsField=0;

void setRot(){ oled.setRotation(flip?2:0); }
void go(State s){ st=s; stEnter=millis(); menu.open(); }

void deepSleep() {
  oled.clearDisplay(); oled.setTextColor(SSD1306_WHITE); oled.setTextSize(1);
  oled.setCursor(18,28); oled.print("Nico foi dormir...");
  oled.display(); delay(700);
  oled.ssd1306_command(SSD1306_DISPLAYOFF);
  nico.doSleep(); nico.save();
  const int wk[5] = {PIN_UP,PIN_DOWN,PIN_LEFT,PIN_RIGHT,PIN_A};
  uint64_t mask=0;
  for (int i=0;i<5;i++){ gpio_pullup_en((gpio_num_t)wk[i]); gpio_pulldown_dis((gpio_num_t)wk[i]); mask|=(1ULL<<wk[i]); }
  esp_deep_sleep_enable_gpio_wakeup(mask, ESP_GPIO_WAKEUP_GPIO_LOW);
  esp_deep_sleep_start();   // acorda = reinicia no boot
}

void setup() {
  Serial.begin(115200);
  randomSeed(esp_random());
  sys.begin("sys", false);
  flip = sys.getBool("flip", true);           // tela certa por padrão
  clockStyle = sys.getInt("cstyle", 0); clockAuto = sys.getInt("cauto", 1);
  clk::restore(sys);
  Wire.begin(PIN_SDA, PIN_SCL);
  if (!oled.begin(SSD1306_SWITCHCAPVCC, 0x3C)) oled.begin(SSD1306_SWITCHCAPVCC, 0x3D);
  setRot(); oled.setTextWrap(false);
  in.begin(); nico.begin();
  bool woke = (esp_sleep_get_wakeup_cause()==ESP_SLEEP_WAKEUP_GPIO);
  if (woke) nico.wake();
  stEnter = millis();
}

// ---------- HUD comum (room scenes) ----------
void hud() {
  // 4 necessidades: ícone + 4 bolinhas (cada uma = 25%). Pisca quando tá baixo.
  const char K[4]={'f','d','h','b'}; float V[4]={nico.hunger,nico.hygiene,nico.happy,nico.energy};
  oled.fillRect(0,0,OLED_W,10,SSD1306_BLACK);
  for (int i=0;i<4;i++){
    int x=1+i*24; bool low=V[i]<25;
    if (!low || (millis()/300)%2) ui::icon(oled,x,1,K[i]);
    int lv=(int)ceilf(V[i]/25.0f);
    for (int k=0;k<4;k++){ int px=x+10+k*4;
      if (k<lv) oled.fillRect(px,3,3,3,SSD1306_WHITE); else oled.drawPixel(px+1,4,SSD1306_WHITE); }
  }
  ui::coinHUD(oled, nico.coins);
  oled.drawFastHLine(0,10,OLED_W,SSD1306_WHITE);
}

// ---------- BOOT ----------
void drawBoot() {
  uint32_t t=millis()-stEnter;
  oled.clearDisplay();
  ui::room(oled, millis(), false);
  nico.x = 64; nico.act = A_HAPPY; nico.actUntil = millis()+9999;
  nico.draw(oled, millis());
  oled.setTextColor(SSD1306_WHITE); oled.setTextSize(2);
  oled.setCursor(28,2); oled.print("NicoOS");
  if (t>1000 && (t/400)%2){ oled.setTextSize(1); oled.setCursor(30,44); oled.print("A p/ comecar"); }
  oled.display();
  if ((t>900 && in.pressed[BTN_A]) || t>4000){ nico.act=A_SIT; nico.actUntil=millis()+1500; go(ST_HOME); }
}

// ---------- HOME (quarto) ----------
const char* HINTS[] = {"<> andar", "^ carinho", "v deitar", "B chamar", "A menu"};
void drawHome() {
  oled.clearDisplay();
  ui::room(oled, millis(), nico.act==A_SLEEP);
  nico.draw(oled, millis());
  hud();
  uint32_t since = millis()-stEnter;
  if (since < 10000) {                                   // dicas dos controles nos primeiros 10s
    const char* h = HINTS[(since/2000)%5]; int w=strlen(h)*6+6;
    oled.fillRoundRect(OLED_W-w-1,12,w,10,3,SSD1306_BLACK); oled.drawRoundRect(OLED_W-w-1,12,w,10,3,SSD1306_WHITE);
    oled.setTextColor(SSD1306_WHITE); oled.setTextSize(1); oled.setCursor(OLED_W-w+2,13); oled.print(h);
  }
  toast.draw(oled);
  oled.display();
  if (in.pressed[BTN_LEFT])  nico.cmdWalk(-1);
  if (in.pressed[BTN_RIGHT]) nico.cmdWalk(1);
  if (in.pressed[BTN_UP])    nico.cmdPet();
  if (in.pressed[BTN_DOWN])  nico.cmdLie();
  if (in.pressed[BTN_B])     nico.cmdCall();
  if (in.pressed[BTN_A])     go(ST_MENU);
}

// ---------- MENU ----------
const char* M_MAIN[] = {"Cuidar","Loja","Brincar","Ferramentas","Dormir","Status","Ajustes"};
void drawMenu() {
  menu.nav(in,7); menu.draw(oled,"NicoOS",M_MAIN,7,nullptr,"psgtzio");
  oled.display();
  if (in.pressed[BTN_B]) go(ST_HOME);
  if (in.pressed[BTN_A]) switch(menu.sel){
    case 0: go(ST_CARE); break; case 1: go(ST_SHOP); break; case 2: go(ST_GAMES); break;
    case 3: go(ST_TOOLS); break; case 4: go(ST_SLEEPMENU); break; case 5: go(ST_STATUS); break;
    case 6: go(ST_SETTINGS); break; }
}

// ---------- CUIDAR ----------
const char* M_CARE[] = {"Dar carinho","Dar banho","Ninar","Voltar"};
void drawCare() {
  menu.nav(in,4); menu.draw(oled,"Cuidar",M_CARE,4,nullptr,"hdzx");
  toast.draw(oled); oled.display();
  if (in.pressed[BTN_B]) go(ST_MENU);
  if (in.pressed[BTN_A]) switch(menu.sel){
    case 0: nico.doPlayJoy(8); toast.show("ronrom <3"); nico.save(); go(ST_HOME); break;
    case 1: nico.doBath(); toast.show("banho!"); nico.save(); go(ST_HOME); break;
    case 2: nico.doSleep(); toast.show("boa noite"); nico.save(); go(ST_HOME); break;
    case 3: go(ST_MENU); break; }
}

// ---------- LOJA ----------
struct Item { const char* name; const char* price; int cost; int stat; int amount; };
// stat: 0=fome 1=higiene 2=feliz
Item SHOP[] = {
  {"Racao",     "5",  5,  0, 18},
  {"Peixe",     "12", 12, 0, 40},
  {"Bolo gato", "20", 20, 0, 70},
  {"Sabonete",  "10", 10, 1, 45},
  {"Brinquedo", "15", 15, 2, 35},
};
const int SHOP_N = 5;
const char* SHOP_NAMES[SHOP_N]; const char* SHOP_PRICES[SHOP_N];
void drawShop() {
  for (int i=0;i<SHOP_N;i++){ SHOP_NAMES[i]=SHOP[i].name; SHOP_PRICES[i]=SHOP[i].price; }
  menu.nav(in,SHOP_N); menu.draw(oled,"Loja",SHOP_NAMES,SHOP_N,SHOP_PRICES,"fffdg");
  { char cb[10]; snprintf(cb,10,"%lu$",(unsigned long)nico.coins); int w=strlen(cb)*6;
    oled.setTextColor(SSD1306_BLACK); oled.setCursor(OLED_W-w-2,3); oled.print(cb); }
  toast.draw(oled); oled.display();
  if (in.pressed[BTN_B]) go(ST_MENU);
  if (in.pressed[BTN_A]) {
    Item &it = SHOP[menu.sel];
    if (!nico.spend(it.cost)) { toast.show("sem moedas!"); return; }
    if (it.stat==0) nico.doEat(it.amount);
    else if (it.stat==1) nico.doBath();
    else nico.doPlayJoy(it.amount);
    toast.show("comprou!"); nico.save(); go(ST_HOME);
  }
}

// ---------- BRINCAR ----------
const char* M_GAMES[] = {"Nico Kart","Flappy Nico","Snake","Pega-petisco","Pulo Arranhador","Voltar"};
void drawGames() {
  menu.nav(in,6); menu.draw(oled,"Brincar",M_GAMES,6,nullptr,"gggggx");
  { char cb[10]; snprintf(cb,10,"%lu$",(unsigned long)nico.coins); int w=strlen(cb)*6;
    oled.setTextColor(SSD1306_BLACK); oled.setCursor(OLED_W-w-2,3); oled.print(cb); }
  oled.display();
  if (in.pressed[BTN_B]) go(ST_MENU);
  if (in.pressed[BTN_A]) switch(menu.sel){
    case 0: kart.begin(); st=ST_KART; break;
    case 1: flappy.begin(); st=ST_FLAPPY; break;
    case 2: snake.begin(); st=ST_SNAKE; break;
    case 3: catchg.begin(); st=ST_CATCH; break;
    case 4: jumpg.begin(); st=ST_JUMP; break;
    case 5: go(ST_MENU); break; }
}
void endGame(int score){
  if (score>0){ nico.addCoins(score); nico.doPlayJoy(min(20,score)); char b[20]; snprintf(b,20,"+%d moedas!",score); toast.show(b); }
  nico.save(); go(ST_GAMES);
}

// ---------- FERRAMENTAS ----------
const char* M_TOOLS[] = {"Rede do Nico","QR do guia","Clima (em breve)","Voltar"};
void drawTools() {
  menu.nav(in,4); menu.draw(oled,"Ferramentas",M_TOOLS,4,nullptr,"wqkx"); oled.display();
  if (in.pressed[BTN_B]) go(ST_MENU);
  if (in.pressed[BTN_A]) switch(menu.sel){
    case 0: go(ST_WIFI_PICK); break; case 1: go(ST_QR); break;
    case 2: toast.show("em breve :)"); break; case 3: go(ST_MENU); break; }
}
void drawWifiPick() {
  menu.nav(in,SSID_COUNT); menu.draw(oled,"Escolha a rede",SSID_NAMES,SSID_COUNT,nullptr,"wwwwww"); oled.display();
  if (in.pressed[BTN_B]) go(ST_TOOLS);
  if (in.pressed[BTN_A]){ ap.start(menu.sel); go(ST_WIFI_ON); }
}
void drawWifiOn() {
  ap.handle();
  oled.clearDisplay(); ui::header(oled,"Rede no ar!");
  oled.setTextColor(SSD1306_WHITE); oled.setTextSize(1);
  oled.setCursor(2,18); oled.print("SSID:"); oled.setCursor(2,28); oled.print(SSID_NAMES[ap.nameIdx]);
  oled.setCursor(2,40); oled.print("Entre pelo celular"); oled.setCursor(2,50); oled.print("Clientes: "); oled.print(ap.clients());
  oled.setCursor(66,56); oled.print("B: parar");
  // onda wifi
  for (int i=0;i<3;i++) if ((millis()/300)%4>i) oled.drawCircle(OLED_W-12, 24, 3+i*4, SSD1306_WHITE);
  oled.display();
  if (in.pressed[BTN_B]){ ap.stop(); go(ST_TOOLS); }
}
void drawQRScreen() {
  oled.clearDisplay(); drawQR(oled, NICO_URL);
  oled.setTextColor(SSD1306_WHITE); oled.setTextSize(1);
  oled.setCursor(0,8); oled.print("Guia"); oled.setCursor(0,18); oled.print("NicoOS");
  oled.setCursor(0,52); oled.print("B:sair"); oled.display();
  if (in.pressed[BTN_B]) go(ST_TOOLS);
}

// ---------- STATUS ----------
void drawStatus() {
  oled.clearDisplay(); ui::header(oled,"Status do Nico");
  const char K[4]={'f','d','h','b'}; const char* L[4]={"Fome","Banho","Feliz","Pilha"};
  float V[4]={nico.hunger,nico.hygiene,nico.happy,nico.energy};
  for (int i=0;i<4;i++){
    int y=15+i*10;
    ui::icon(oled,2,y,K[i]);
    oled.setTextColor(SSD1306_WHITE); oled.setTextSize(1); oled.setCursor(12,y); oled.print(L[i]);
    oled.drawRoundRect(44,y,58,8,3,SSD1306_WHITE);
    int w=(int)(V[i]/100*54); if (w>0) oled.fillRoundRect(46,y+2,w,4,1,SSD1306_WHITE);
    char b[6]; snprintf(b,6,"%d%%",(int)V[i]); oled.setCursor(106,y); oled.print(b);
  }
  oled.setCursor(2,56); oled.print(nico.age/60); oled.print("h de vida");
  ui::icon(oled,84,56,'c'); oled.setCursor(94,56); oled.print(nico.coins);
  oled.display();
  if (in.pressed[BTN_A]||in.pressed[BTN_B]) go(ST_MENU);
}

// ---------- DORMIR ----------
const char* M_SLEEP[] = {"Cochilo (tela off)","Desligar (deep sleep)","Voltar"};
void drawSleepMenu() {
  menu.nav(in,3); menu.draw(oled,"Dormir",M_SLEEP,3,nullptr,"zzx"); oled.display();
  if (in.pressed[BTN_B]) go(ST_MENU);
  if (in.pressed[BTN_A]) switch(menu.sel){
    case 0: nico.doSleep(); oled.ssd1306_command(SSD1306_DISPLAYOFF); go(ST_NAP); break;
    case 1: deepSleep(); break;
    case 2: go(ST_MENU); break; }
}
void drawNap() {
  // tela apagada; qualquer botão acorda
  if (in.anyDown()){ oled.ssd1306_command(SSD1306_DISPLAYON); nico.wake(); toast.show("acordou!"); go(ST_HOME); }
}

// ---------- AJUSTES ----------
const char* M_SET[] = {"Relogio","Virar tela","Resetar Nico","Sobre","Voltar"};
void drawSettings() {
  menu.nav(in,5); menu.draw(oled,"Ajustes",M_SET,5,nullptr,"lorix");
  if (confirmReset){ oled.fillRoundRect(8,20,112,26,4,SSD1306_BLACK); oled.drawRoundRect(8,20,112,26,4,SSD1306_WHITE);
    oled.setTextColor(SSD1306_WHITE); oled.setCursor(14,24); oled.print("Resetar o Nico?"); oled.setCursor(14,35); oled.print("A=sim  B=nao"); }
  toast.draw(oled); oled.display();
  if (confirmReset){ if(in.pressed[BTN_A]){nico.reset();confirmReset=false;toast.show("Nico renasceu!");} if(in.pressed[BTN_B])confirmReset=false; return; }
  if (in.pressed[BTN_B]) go(ST_MENU);
  if (in.pressed[BTN_A]) switch(menu.sel){
    case 0: go(ST_CLOCKMENU); break;
    case 1: flip=!flip; sys.putBool("flip",flip); setRot(); toast.show("tela virada!"); break;
    case 2: confirmReset=true; break;
    case 3: toast.show("NicoOS v" NICO_VERSION); break;
    case 4: go(ST_MENU); break; }
}

// ---------- RELÓGIO ----------
char cmA[20], cmB[22];
void drawClockMenu() {
  snprintf(cmA,20,"Estilo: %s",STYLE_N[clockStyle]);
  if (clockAuto==0) snprintf(cmB,22,"Auto: desligado"); else snprintf(cmB,22,"Auto: %ds parado",AUTO_S[clockAuto]);
  const char* items[5] = {"Ver relogio", cmA, "Acertar hora", cmB, "Voltar"};
  menu.nav(in,5); menu.draw(oled,"Relogio",items,5,nullptr,"lolox");
  toast.draw(oled); oled.display();
  if (in.pressed[BTN_B]) go(ST_SETTINGS);
  bool l=in.pressed[BTN_LEFT], r=in.pressed[BTN_RIGHT], a=in.pressed[BTN_A];
  if (menu.sel==1 && (a||l||r)) { clockStyle=(clockStyle+(l?2:1))%3; sys.putInt("cstyle",clockStyle); }
  if (menu.sel==3 && (a||l||r)) { clockAuto=(clockAuto+(l?3:1))%4; sys.putInt("cauto",clockAuto); }
  if (a && menu.sel==0) { clockReturn=ST_CLOCKMENU; st=ST_CLOCK; stEnter=millis(); }
  if (a && menu.sel==2) { tm t=clk::now(); tsH=t.tm_hour; tsM=t.tm_min; tsField=0; st=ST_TIMESET; stEnter=millis(); }
  if (a && menu.sel==4) go(ST_SETTINGS);
}
void drawClock() {
  clk::draw(oled, clockStyle, millis());
  if (millis()-stEnter > 400 && (in.pressed[BTN_A]||in.pressed[BTN_B]||in.pressed[BTN_UP]||in.pressed[BTN_DOWN])) go(clockReturn);
  if (in.pressed[BTN_LEFT])  clockStyle=(clockStyle+2)%3;
  if (in.pressed[BTN_RIGHT]) clockStyle=(clockStyle+1)%3;
}
void drawTimeSet() {
  oled.clearDisplay(); ui::header(oled,"Acertar hora");
  int x=20,y=20;
  clk::seg7(oled,x,y,tsH/10); clk::seg7(oled,x+18,y,tsH%10);
  oled.fillRect(x+38,y+7,3,3,SSD1306_WHITE); oled.fillRect(x+38,y+17,3,3,SSD1306_WHITE);
  clk::seg7(oled,x+46,y,tsM/10); clk::seg7(oled,x+64,y,tsM%10);
  if ((millis()/300)%2) oled.fillRect(tsField==0?x:x+46, y+29, 32, 2, SSD1306_WHITE);
  oled.setTextColor(SSD1306_WHITE); oled.setTextSize(1); oled.setCursor(100,24); oled.print("A:ok");
  oled.setCursor(100,36); oled.print("B:x");
  oled.display();
  if (in.pressed[BTN_LEFT]||in.pressed[BTN_RIGHT]) tsField^=1;
  int d = in.pressed[BTN_UP]?1:(in.pressed[BTN_DOWN]?-1:0);
  if (d){ if(tsField==0) tsH=(tsH+d+24)%24; else tsM=(tsM+d+60)%60; }
  if (in.pressed[BTN_A]){ clk::setLocal(sys,tsH,tsM); toast.show("hora acertada!"); go(ST_CLOCKMENU); }
  if (in.pressed[BTN_B]) go(ST_CLOCKMENU);
}

void loop() {
  in.poll();
  nico.update();
  bool anyIn=false; for(int i=0;i<BTN_COUNT;i++) if(in.down[i]) anyIn=true;
  if (anyIn) lastInput=millis();
  if (st==ST_HOME && clockAuto>0 && millis()-lastInput > AUTO_S[clockAuto]*1000UL) { clockReturn=ST_HOME; st=ST_CLOCK; stEnter=millis(); }
  if (millis()-lastTimeSave>60000){ clk::persist(sys); lastTimeSave=millis(); }
  if (millis()-lastSave>30000){ nico.save(); lastSave=millis(); }
  switch (st) {
    case ST_BOOT:      drawBoot(); break;
    case ST_HOME:      drawHome(); break;
    case ST_MENU:      drawMenu(); break;
    case ST_CARE:      drawCare(); break;
    case ST_SHOP:      drawShop(); break;
    case ST_GAMES:     drawGames(); break;
    case ST_SNAKE:     if (snake.step(in,oled))  endGame(snake.score); break;
    case ST_CATCH:     if (catchg.step(in,oled)) endGame(catchg.score); break;
    case ST_FLAPPY:    if (flappy.step(in,oled)) endGame(flappy.score); break;
    case ST_JUMP:      if (jumpg.step(in,oled))  endGame(jumpg.points()); break;
    case ST_KART:      if (kart.step(in,oled))   endGame(kart.score()); break;
    case ST_TOOLS:     drawTools(); break;
    case ST_WIFI_PICK: drawWifiPick(); break;
    case ST_WIFI_ON:   drawWifiOn(); break;
    case ST_QR:        drawQRScreen(); break;
    case ST_STATUS:    drawStatus(); break;
    case ST_SLEEPMENU: drawSleepMenu(); break;
    case ST_NAP:       drawNap(); break;
    case ST_SETTINGS:  drawSettings(); break;
    case ST_CLOCK:     drawClock(); break;
    case ST_CLOCKMENU: drawClockMenu(); break;
    case ST_TIMESET:   drawTimeSet(); break;
  }
  delay(8);
}
