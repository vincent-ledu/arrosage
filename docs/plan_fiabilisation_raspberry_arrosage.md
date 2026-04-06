# Fiabilisation d’une installation Raspberry Pi (arrosage) — Plan & Schémas

## Objectif
Rendre l’installation **modulaire, maintenable et fiable** en extérieur :
- Retirer le Raspberry sans dessouder
- Tester chaque bloc indépendamment
- Séparer basse tension / 230V
- Réduire les faux contacts et parasites

---

## Architecture cible

```
Raspberry Pi
   ↓ (nappe 40 pins)
Breakout GPIO à vis
   ↓
 ├── Bloc capteurs (flotteurs)
 └── Bloc relais (pompe + électrovanne)

Banc de test séparé :
 ├── Interrupteurs (simulation flotteurs)
 └── LEDs (simulation sorties)
```

---

## Règles générales

### Types de fils
- **AWG22 (≈0.34 mm²)** → tous les signaux (GPIO, capteurs, relais)
- **1.5 mm²** → uniquement le 230V

### Connexions
- ✔ Borniers à vis → partout
- ✔ Ferrules (embouts) → sur tous les fils AWG22
- ❌ Dupont → uniquement pour banc de test
- ❌ Soudure → éviter dans la boîte finale

---

## Étape 1 — Breakout GPIO

### Objectif
Supprimer toute connexion directe fragile sur le Raspberry

### Câblage
```
Raspberry Pi
   ↓ nappe 40 pins
Breakout GPIO à vis
```

---

## Étape 2 — Bloc capteurs (flotteurs)

### Schéma logique (pull-up)

```
3.3V ──[10kΩ]── GPIO ─── flotteur ─── GND
```

### Câblage réel

```
[Flotteur]
   ↓ (AWG22)
Bornier capteurs
   ↓
Breakout GPIO
```

### Connexions
- Flotteur → GPIO (via bornier)
- Flotteur → GND
- Résistance 10kΩ entre GPIO et 3.3V

### Mise en œuvre
- Résistances sur petite plaque proto
- Tous les fils AWG22 avec ferrules
- Tout vissé (pas de fils nus)

---

## Étape 3 — Bloc relais (pompe + électrovanne)

### Basse tension

```
GPIO ─── IN1 relais (pompe)
GPIO ─── IN2 relais (vanne)

5V ─── VCC relais
GND ─── GND relais
```

### 230V

```
Phase ─── COM relais
NO ─── pompe / vanne
Neutre ─── direct
Terre ─── direct (si applicable)
```

### Fils
- GPIO → AWG22
- 230V → 1.5 mm²

### Connexions
- Tout vissé
- Aucun fil soudé côté puissance

---

## Étape 4 — Organisation du boîtier

### Séparation obligatoire

```
[ Zone basse tension ]
- Raspberry
- Breakout
- Capteurs

[ Zone 230V ]
- Relais
- Pompe
- Électrovanne
```

### Bonnes pratiques
- Presse-étoupes
- Fils fixés
- Aucun fil en traction

---

## Étape 5 — Banc de test

### Schéma

```
Interrupteur ─── GPIO ─── GND
GPIO ─── LED ─── résistance ─── GND
```

### Matériel
- 4 interrupteurs (flotteurs)
- 2 LEDs (sorties)
- résistances 220Ω

---

## Étape 6 — Ordre de migration

1. Créer le banc de test
2. Installer breakout GPIO
3. Refaire bloc capteurs
4. Refaire bloc relais
5. Réorganiser boîtier

---

## Résultat attendu

- Raspberry extractible rapidement
- Diagnostic facile
- Moins de parasites
- Installation durable extérieur
