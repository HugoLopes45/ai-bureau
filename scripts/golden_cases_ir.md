# Golden cases — `calcul_ir.py` vs. simulateur officiel

Procédure de vérification des valeurs attendues dans `test_calcul_ir.py` contre
le simulateur DGFiP officiel. Objectif : **chaque valeur "attendue" du test
doit pouvoir être retracée à une saisie dans le simulateur, avec URL et date**.

Tant que ce fichier n'est pas rempli, les valeurs attendues de `test_calcul_ir.py`
ne sont que des **tests de non-régression** — ils prouvent que le calculateur
n'a pas changé, pas qu'il est conforme à l'impôt réel.

---

## Simulateur officiel

**URL** : https://www.impots.gouv.fr/simulateur-ir-mensualisation
**Version utilisée** : simulateur 2026 (revenus 2025)
**À saisir en mode "Simplifié"** sauf mention contraire.

---

## Cas à vérifier

Pour chaque cas : aller sur le simulateur, saisir les champs, noter l'IR net
affiché ("Montant de votre impôt sur le revenu"), reporter dans le tableau
ci-dessous. Si écart > 5 € avec la valeur calculée par `calcul_ir.py`,
**bloquer le merge** et investiguer la source de l'écart.

### Cas 1 — Célibataire, salaires moyens (tranche 30 %)

**Saisie simulateur** :
- Situation : célibataire, 1 part
- Salaires nets imposables : `45 000 €`

**Calcul (barème 2026, loi n° 2026-103)** :
- 11 600 → 29 579 : 17 979 × 11 % = 1 977,69
- 29 579 → 45 000 : 15 421 × 30 % = 4 626,30
- Brut = 6 603,99 €. Pas de décote.

| Champ | Valeur |
|---|---|
| Calcul `calcul_ir.py` | 6 604 € |
| **Observé simulateur** | _____________ € |
| **Vérifié le** | __________ |

### Cas 2 — Célibataire, décote partielle

**Saisie simulateur** : célibataire, 1 part, salaires 20 000 €.

**Calcul** :
- 11 600 → 20 000 : 8 400 × 11 % = 924
- Décote : max(0, 897 − 45,25 % × 924) = 478,89
- Net = 924 − 478,89 = 445,11 €

| Champ | Valeur |
|---|---|
| Calcul `calcul_ir.py` | 445 € |
| **Observé simulateur** | _____________ € |
| **Vérifié le** | __________ |

### Cas 3 — Couple, pas d'enfant

**Saisie simulateur** : marié(e)/pacsé(e), 2 parts, salaires 40 000 € × 2 = 80 000 € total.

**Calcul** :
- Par part 40 000 : 1 977,69 + 10 421 × 30 % = 5 103,99
- × 2 = 10 207,98 €. Pas de décote.

| Champ | Valeur |
|---|---|
| Calcul `calcul_ir.py` | 10 208 € |
| **Observé simulateur** | _____________ € |
| **Vérifié le** | __________ |

### Cas 4 — Couple + 2 enfants, QF non plafonné

**Saisie simulateur** : marié(e)/pacsé(e), 2 enfants → 3 parts, salaires 40 000 € × 2.

**Calcul** :
- Par part 26 666,67 : (26 666,67 − 11 600) × 11 % = 1 657,33 ; × 3 parts = 4 971,99
- Référence 2 parts 40k par part : 5 103,99 × 2 = 10 207,98
- Gain QF = 5 236 > plafond 3 614 (2 × 1 807) → plafonné
- Net = 10 207,98 − 3 614 = 6 593,98 €

| Champ | Valeur |
|---|---|
| Calcul `calcul_ir.py` | 6 594 € |
| **Observé simulateur** | _____________ € |
| **Vérifié le** | __________ |

### Cas 5 — Couple + 2 enfants, QF plafonné (revenus élevés)

**Saisie simulateur** : marié(e)/pacsé(e), 2 enfants → 3 parts, salaires 100 000 € × 2.

**Calcul** :
- Par part 66 666,67 : 1 977,69 + 37 087,67 × 30 % = 13 103,99 ; × 3 = 39 311,97
- Référence 2 parts 100k par part : 24 800,52 × 2 = 49 601,04
- Gain QF = 10 289 > plafond 3 614 → plafonné
- Net = 49 601,04 − 3 614 = 45 987,04 €

| Champ | Valeur |
|---|---|
| Calcul `calcul_ir.py` | 45 987 € |
| **Observé simulateur** | _____________ € |
| **Vérifié le** | __________ |

---

## Procédure après vérification

1. Remplir les 5 cases "Observé simulateur" et "Vérifié le" ci-dessus.
2. Calculer l'écart : `observé − calculé`.
3. Si tous les écarts ≤ 5 € → **ajouter dans chaque cas de `test_calcul_ir.py`
   la mention** `# Vérifié vs. simulateur impots.gouv.fr le YYYY-MM-DD`.
4. Si un écart > 5 € :
   - Vérifier que la saisie simulateur est correcte (champs, situation, parts).
   - Vérifier `data/rates/ir_2026.json` : barème, plafond QF, seuils décote.
   - Si l'écart persiste, ouvrir une issue / noter la divergence ici avec
     hypothèse (abattement manquant ? crédit d'impôt appliqué par le
     simulateur mais pas par le calculateur ?).
5. Re-vérifier à chaque **changement du barème** (loi de finances annuelle,
   en général début février).

---

## Limites connues de `calcul_ir.py` (ne pas attendre correspondance)

- **CEHR** (Contribution Exceptionnelle sur les Hauts Revenus, CGI art. 223 sexies) :
  3 % / 4 % au-dessus de 250 k€ / 500 k€ célibataire, 500 k€ / 1 M€ couple.
  Pas implémentée dans `calcul_ir.py`. Attendre un écart croissant au-delà
  de ces seuils.
- **Crédits et réductions d'impôt** (emploi à domicile, dons, PER au-delà du
  plafond déductible, etc.) : non appliqués ici. Le simulateur les applique
  dès que les champs sont saisis — s'assurer qu'on saisit les mêmes données
  (0 partout sauf salaires).
- **Abattements spécifiques** (journalistes, pensions, etc.) : non appliqués.

Pour les comparaisons, saisir au simulateur **seulement des salaires**, pas
d'autres revenus, pas de crédits d'impôt.
