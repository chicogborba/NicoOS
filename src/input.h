// NicoOS — leitura de botões com debounce, borda e auto-repeat
#pragma once
#include "config.h"

struct Input {
  bool down[BTN_COUNT]    = {false};
  bool pressed[BTN_COUNT] = {false};  // borda: só no instante do aperto (com repeat)
  uint32_t since[BTN_COUNT] = {0};
  uint32_t lastRepeat[BTN_COUNT] = {0};
  bool raw[BTN_COUNT] = {false};
  uint32_t rawSince[BTN_COUNT] = {0};

  void begin() {
    for (int i = 0; i < BTN_COUNT; i++) pinMode(BTN_PIN[i], INPUT_PULLUP);
  }

  void poll() {
    uint32_t now = millis();
    for (int i = 0; i < BTN_COUNT; i++) {
      pressed[i] = false;
      bool r = (digitalRead(BTN_PIN[i]) == LOW);
      if (r != raw[i]) { raw[i] = r; rawSince[i] = now; }       // debounce 15ms
      if (now - rawSince[i] >= 15 && r != down[i]) {
        down[i] = r;
        since[i] = now;
        if (r) { pressed[i] = true; lastRepeat[i] = now; }      // aperto novo
      }
      // auto-repeat para direcionais (segurar)
      if (down[i] && (i == BTN_UP || i == BTN_DOWN || i == BTN_LEFT || i == BTN_RIGHT)) {
        if (now - since[i] > 380 && now - lastRepeat[i] > 120) {
          pressed[i] = true; lastRepeat[i] = now;
        }
      }
    }
  }

  bool anyDown() { for (int i=0;i<BTN_COUNT;i++) if (down[i]) return true; return false; }
};
