# BINI Cat Handheld — mod paramétrico do "Printble Gaming Device"

Base: GrabCAD *printble gaming device* (pinabini). Geometria original medida das STLs
(`uper cover`, `lower cover`, `mirror holder`, botões) e regenerada parametricamente
com o novo estilo + eletrônica nova.

```
python build.py                                   # gera tudo + checagem de colisão (≈8 s)
blender -b -P render_blender.py -- "$PWD/out"     # renders opcionais
```
Edite **só `params.py`**. Tudo marcado `# CONFIRM` deve ser medido no componente real.

## O que foi preservado do original
| Original | Mod |
|---|---|
| Footprint 56.2 × 76.2 mm | igual (+ orelhas, 86.2 total) |
| 2 cascas: superior (tela+botões) / inferior com encaixe por lingueta + snap | igual (lingueta 1.0 mm, 2 snaps laterais) |
| Perfboard aparafusada em 4 bosses na casca superior | igual (M2 auto-atarraxante) — bosses movidos ~1.6 mm p/ dentro por causa dos cantos R9 |
| Janela da tela 41.4 × 26.6 na mesma posição + moldura preta encaixada por dentro ("mirror holder") | igual (`screen_bezel`) |
| D-pad 4 botões quadrados, pitch 7.6, recesso em cruz | igual |
| A/B redondos em recesso pílula, mesmas posições | igual; Ø 7.4 (orig. deixava parede de 0.8 mm entre furos → agora 1.2 mm) |
| USB-C na borda inferior | agora 2 portas simétricas (TP4056 carga / ESP32 programação) |

## Estilo
Cantos em planta R9, bordas "pillow" (frente R6, trás R3.5), face frontal num único plano,
orelhas de gato integradas ao contorno com filete suave (espessura total → imprimem sem suporte).
Os primeiros 29 % de cada filete encostado na mesa viram chanfro 45° (imprime limpo, visualmente idêntico).

## Empilhamento (z, mm a partir das costas)
| z | |
|---|---|
| 0 → 2.2 | parede traseira |
| 2.2 → 7.2 | bateria (5 mm) deitada no fundo, 1.5 mm de folga lateral/superior |
| 6.23 | **linha de features**: centro das USB-C e do switch |
| 5.5 | centro do LED IR e receptor IR |
| 10.75 | linha de divisão das cascas (lingueta até 12.75) |
| 10.7 → 12.3 | PCB principal (2 mm de keep-out embaixo para soldas) |
| 16.6 | topo do plunger do tact 6×6×4.3 |
| 17.85 → 20.05 | parede frontal |

Espessura total **20.05 mm** (original 24).

## Layout interno (casca traseira)
- **TP4056** (x −10.5) e **ESP32-C3 Super Mini** (x +10.5) com USB-C na borda inferior, trilhos de 0.8 mm, guias laterais e batente traseiro. Fixar com fita dupla-face fina.
  Porta: abertura 10.1 × 4.5 + rebaixo externo 12.8 × 7.0 × 1.4 para o corpo do cabo encostar no conector.
- **Bateria 502535** (~400 mAh) no centro, 4 nervuras em L de 3 mm (mais baixas que a célula → sai fácil, nunca é prensada). 402535 / 503035 cabem trocando os parâmetros.
- **LED IR** (x −5) e **receptor IR** (x +5) na borda de cima, entre as orelhas, mesmo Ø de janela (simétrico). LED encaixa por cima num berço em U com batente; receptor num bolso aberto para os terminais.
- **Chave liga/desliga** (opcional, `POWER_SWITCH`) na lateral direita, perto do topo.
- Canais livres para fios: parede esquerda, faixa acima da bateria, e 2 entalhes na PCB (y −12) para subir até a PCB principal.

## Montagem sem parafuso
- A PCB principal fica em "sanduíche": 2 pinos-guia (Ø2.0) em bosses diagonais da casca frontal posicionam a placa;
  9 apoios em 45° nas paredes da casca traseira encostam por baixo (folga 0.1 mm) quando o case fecha.
- Fechamento: lingueta + 4 travas de encaixe (2 por lado). Abrir: unha/palheta na fenda da borda inferior, entre as USB.
- Parafusos M2×6 viraram opcionais: só os 2 bosses sem pino têm furo. Deixam a placa presa na casca frontal mesmo com o case aberto.
- Não soldar nada nos 1.6 mm da borda de baixo da PCB (onde os apoios encostam).
- Ajustes: `PCB_CLAMP_GAP` (0 = mais firme), `SNAP_BUMP` (maior = fecha mais duro), `PCB_PIN_BOSSES = ()` volta aos 4 parafusos.

## Tampa da porta do ESP32 + ícone de carga
- `usb_cap_esp32`: placa que preenche o rebaixo da porta do ESP32 rente à casca (segue a curvatura),
  + gola que encaixa na abertura + luva com fenda para a língua central que entra 3 mm **dentro** da USB-C (fixação por atrito).
  Meia-lua na ponta direita para tirar com a unha. Aperto ajustável: `USB_CAP_SLEEVE_FIT` (menor = mais justo).
  Imprimir com a face pra baixo; luva tem paredes de ~0.7 mm → bico 0.4, 2 perímetros.
- Raio ⚡ gravado 0.35 mm na borda inferior, acima da porta de carga (TP4056), dentro da faixa reta da casca frontal
  (altura limitada a 2.7 mm para não cruzar a emenda nem a curva). `CHARGE_ICON = False` remove.

## Arquivos (`out/`)
- `print/front_shell_FACE_DOWN.stl` — face na mesa, sem suporte
- `print/back_shell.stl` — costas na mesa, sem suporte
- `print/screen_bezel_FACE_DOWN.stl` — imprimir em preto
- `print/buttons_x6.stl` — 4 D-pad + 2 A/B, flange na mesa
- `print/usb_cap_esp32_FACE_DOWN.stl` — tampa da porta de programação, mesma cor da casca
- `assembly/*.stl` — tudo em coordenadas de montagem, inclusive dummies dos componentes (`cmp_*`)
- `mainboard_template.svg` — gabarito 1:1 da perfboard (contorno, furos M2 Ø2.2, tacts, OLED). Imprimir em 100 %.
- `validation.md` — checagem virtual de folgas

## Checagem virtual (resumo)
Todas as combinações componente×componente e componente×casca testadas por interseção booleana,
mais envelopes de folga (bateria +1.5 mm, keep-out da PCB, canais de fio, folga ESP/TP, plug USB-C inserido).
**0 falhas.** Detalhe em `out/validation.md`.

## Medir quando as peças chegarem (`# CONFIRM`)
ESP32-C3 SM (18 × 22.52 × 1.0, overhang do USB), TP4056 USB-C (17.5 × 28 × 1.6 — há versões 26 mm e PCB 1.2),
bateria, LED IR (5 mm, comprimento até a flange), receptor (VS1838B/TSOP: face 6 × 7, domo), chave SS12D00,
módulo OLED 0.96" (altura total com header deve ser ≤ 5.55 mm; se menor, calço/espuma).

## Notas elétricas (não assumidas pelo modelo)
- Carga **só** pela USB do TP4056. A USB do ESP32 é para programação/debug.
- TP4056 (versão com proteção DW01) OUT+ → chave → pino **5V** do ESP32-C3 (passa pelo LDO da placa).
  Ligar as duas USB ao mesmo tempo pode realimentar VBUS do ESP na saída do TP4056/bateria — use um Schottky
  (ex. SS14) em série no OUT+, ou desligue a chave ao programar. Verifique o esquema da sua placa.
- LED IR precisa de driver (NPN/MOSFET + resistor), GPIO não aguenta os ~50–100 mA de pulso.
- GPIO: 6 botões + I²C (2) + IR TX + IR RX + divisor de bateria (100k/100k) = 11 dos 13 livres. Evite GPIO2/8/9 (strapping) para botões.
- Parafusos: 4× M2 × 6 auto-atarraxante (PCB → bosses). Casca traseira só encaixa (abre pela fenda inferior entre as USB).
