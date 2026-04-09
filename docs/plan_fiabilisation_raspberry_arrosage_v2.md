# Plan de fiabilisation Raspberry Pi arrosage (v2)

## 🔋 Condensateurs

### 5V relais
5V ───┬──[100nF]── GND
      │
      └──[470µF]── GND

### 3.3V capteurs
3.3V ───┬──[100nF]── GND
        │
        └──[100µF]── GND

### GPIO flotteurs
GPIO ───┬── flotteur ─── GND
        │
       [100nF]
        │
       GND

### 230V
Snubber RC sur charge
