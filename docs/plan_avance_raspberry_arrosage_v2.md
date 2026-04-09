# Plan avancé Raspberry Pi arrosage (v2)

## 🔋 Schéma condensateurs

5V ───┬──[100nF]── GND
      │
      └──[470µF]── GND

3.3V ───┬──[100nF]── GND
        │
        └──[100µF]── GND

GPIO ───┬── flotteur ─── GND
        │
       [100nF]
        │
       GND

230V : snubber RC parallèle
