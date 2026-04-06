# Fiabilisation avancée installation Raspberry Pi arrosage

## 🎯 Objectif
Version robuste, maintenable, testable avec :
- mapping GPIO clair
- code couleur câblage
- schémas électriques détaillés

---

# 🧠 1. Mapping GPIO recommandé

| Fonction | GPIO BCM | Pin physique |
|----------|----------|--------------|
| Flotteur 1 (bas) | GPIO17 | Pin 11 |
| Flotteur 2 | GPIO27 | Pin 13 |
| Flotteur 3 | GPIO22 | Pin 15 |
| Flotteur 4 (haut) | GPIO23 | Pin 16 |
| Relais pompe | GPIO24 | Pin 18 |
| Relais vanne | GPIO25 | Pin 22 |
| GND | - | Pins 6, 9, 14 |
| 3.3V | - | Pin 1 |
| 5V | - | Pin 2 |

---

# 🎨 2. Code couleur recommandé

| Signal | Couleur |
|--------|--------|
| 3.3V | Orange |
| 5V | Rouge |
| GND | Noir |
| Entrées flotteurs | Bleu |
| Sorties relais | Jaune |
| 230V phase | Marron |
| 230V neutre | Bleu |
| Terre | Vert/Jaune |

---

# 🔌 3. Schéma bloc complet

```
[Flotteurs] 
   ↓
[Bornier capteurs]
   ↓
[Breakout GPIO]
   ↓
[Raspberry Pi]

GPIO sorties
   ↓
[Relais]
   ↓
Pompe / électrovanne
```

---

# ⚡ 4. Schéma électrique capteurs

```
3.3V
  │
 [10kΩ]
  │
GPIO ──────── Flotteur ──────── GND
```

### Détail
- Résistance pull-up 10kΩ
- Contact flotteur vers GND

---

# ⚡ 5. Schéma électrique relais

## Partie logique (basse tension)

```
GPIO24 ─── IN1 (pompe)
GPIO25 ─── IN2 (vanne)

5V ─────── VCC relais
GND ────── GND relais
```

## Partie puissance (230V)

```
Phase ─── COM relais
NO ────── Pompe
Neutre ── Pompe direct
Terre ─── Pompe direct
```

---

# 🔧 6. Types de fils

| Usage | Type |
|------|------|
| GPIO / capteurs | AWG22 |
| Alim 5V | AWG22 |
| 230V | 1.5 mm² |

---

# 🧪 7. Banc de test

## Schéma

```
Switch ─── GPIO ─── GND

GPIO ─── LED ─── 220Ω ─── GND
```

---

# 🧱 8. Organisation boîtier

## Zone 1 (basse tension)
- Raspberry
- breakout
- capteurs

## Zone 2 (230V)
- relais
- alimentation secteur

---

# 🧩 9. Bonnes pratiques

- Ferrules sur tous les fils
- Aucun Dupont en prod
- Presse-étoupes obligatoires
- Séparation physique 230V / 3.3V

---

# ✅ 10. Résultat

- Maintenance rapide
- Debug facile
- Fiabilité extérieure
