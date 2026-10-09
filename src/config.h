// NicoOS — pinos e constantes do hardware BINI Cat
#pragma once
#include <Arduino.h>

// ---- Tela OLED (I2C) ----
#define OLED_W      128
#define OLED_H      64
#define PIN_SDA     8
#define PIN_SCL     9
// endereço tentado automaticamente (0x3C e depois 0x3D)

// ---- Botões (INPUT_PULLUP, apertado = LOW) ----
#define PIN_UP      0
#define PIN_DOWN    1
#define PIN_LEFT    3
#define PIN_RIGHT   4
#define PIN_A       5
#define PIN_B       10

enum Btn { BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT, BTN_A, BTN_B, BTN_COUNT };
static const uint8_t BTN_PIN[BTN_COUNT] = { PIN_UP, PIN_DOWN, PIN_LEFT, PIN_RIGHT, PIN_A, PIN_B };

// ---- Bateria (opcional) ----
// Se você soldar um divisor 100k/100k da bateria num GPIO livre, ponha o pino aqui.
// -1 = sem medição (mostra ícone de USB).
#define PIN_BAT_ADC  -1
#define BAT_DIV      2.0f     // (R1+R2)/R2 do divisor
#define BAT_FULL     4.15f
#define BAT_EMPTY    3.30f

// ---- GitHub Pages (QR code) ----
#define NICO_URL     "https://chicogborba.github.io/NicoOS/"

// ---- Versão ----
#define NICO_VERSION "0.4"

// fuso horário (Brasília/Porto Alegre, UTC-3)
#define NICO_TZ "<-03>3"
