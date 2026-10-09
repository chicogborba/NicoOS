// NicoOS — ferramentas de WiFi (captive portal rede-piada) + QR code
#pragma once
#include <WiFi.h>
#include <DNSServer.h>
#include <WebServer.h>
#include <qrcode.h>
#include <Adafruit_SSD1306.h>
#include "config.h"

// nomes de rede engraçados (uma por vez, o usuário escolhe)
static const char* SSID_NAMES[] = {
  "NICO FODA",
  "papoi banana",
  "bello potato",
  "tank yu",
  "miau free wifi",
  "nico ta te vendo",
};
static const int SSID_COUNT = sizeof(SSID_NAMES)/sizeof(SSID_NAMES[0]);

// pagina fofa servida no portal (pixel-art do Nico em CSS)
static const char PORTAL_HTML[] PROGMEM = R"HTML(<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>NICO</title>
<style>
body{margin:0;background:#ffd56b;font-family:monospace;color:#3a2a10;text-align:center;overflow-x:hidden}
h1{font-size:2.2em;margin:18px 0 4px;letter-spacing:2px}
p{margin:4px 18px;font-size:1.05em}
.cat{display:grid;grid-template-columns:repeat(12,14px);gap:0;justify-content:center;margin:20px auto}
.cat i{width:14px;height:14px}
.o{background:#f59e2b}.d{background:#2a1a05}.w{background:#fff}.b{background:transparent}
.card{background:#fff;border:4px solid #2a1a05;border-radius:14px;max-width:320px;margin:18px auto;padding:14px;box-shadow:6px 6px 0 #2a1a05}
a{color:#c2410c;font-weight:bold}
</style></head><body>
<h1>MIAU</h1>
<div class=cat id=c></div>
<div class=card><p>voce entrou na rede do <b>NICO</b> &#128049;</p>
<p>ele e um gato laranja e ele te acha legal.</p>
<p>feito com NicoOS &#128293;</p></div>
<script>
var G=[
"bbooobbbbooob","bodddobboddob","bodddoodd ddo".replace(/ /g,'d'),
"boddddddddddo","boodwdddwdoob","booodddddooob","bbooddddddoob","bbbooooooobbb"];
var m={o:'o',d:'d',w:'w',b:'b'};var c=document.getElementById('c');
G.forEach(r=>{for(const ch of r){var i=document.createElement('i');i.className=m[ch]||'b';c.appendChild(i)}});
</script>
</body></html>)HTML";

struct WifiAP {
  DNSServer dns;
  WebServer *web = nullptr;
  bool on = false;
  int nameIdx = 0;

  void start(int idx) {
    nameIdx = idx;
    WiFi.mode(WIFI_AP);
    WiFi.softAP(SSID_NAMES[idx]);
    IPAddress ip = WiFi.softAPIP();
    dns.start(53, "*", ip);
    web = new WebServer(80);
    web->onNotFound([this](){ web->sendHeader("Location", "http://192.168.4.1/"); web->send(302, "text/plain", ""); });
    web->on("/", [this](){ web->send_P(200, "text/html", PORTAL_HTML); });
    web->begin();
    on = true;
  }
  void handle() { if (on){ dns.processNextRequest(); web->handleClient(); } }
  void stop() {
    if (!on) return;
    dns.stop(); if (web){ web->stop(); delete web; web = nullptr; }
    WiFi.softAPdisconnect(true); WiFi.mode(WIFI_OFF);
    on = false;
  }
  int clients() { return on ? WiFi.softAPgetStationNum() : 0; }
};

// desenha um QR code centralizado para um texto
inline void drawQR(Adafruit_SSD1306 &g, const char* text) {
  QRCode qr;
  static uint8_t buf[256];                        // suficiente p/ versão 3 (29x29)
  qrcode_initText(&qr, buf, 3, ECC_LOW, text);   // versão 3 = 29x29
  int scale = 2;
  int sz = qr.size * scale;
  int ox = (OLED_W - sz) / 2 + 20;   // deslocado p/ caber legenda à esquerda
  int oy = (OLED_H - sz) / 2;
  g.fillRect(ox-2, oy-2, sz+4, sz+4, SSD1306_WHITE); // quiet zone branca
  for (uint8_t y = 0; y < qr.size; y++)
    for (uint8_t x = 0; x < qr.size; x++)
      if (qrcode_getModule(&qr, x, y))
        g.fillRect(ox + x*scale, oy + y*scale, scale, scale, SSD1306_BLACK);
}
