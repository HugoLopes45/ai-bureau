# Golden cases — `calcul_are.py` vs. simulateur officiel

Procédure de vérification des valeurs attendues dans `test_calcul_are.py` contre
le simulateur France Travail officiel. Objectif : **chaque valeur "attendue"
du test doit pouvoir être retracée à une saisie dans le simulateur, avec URL
et date**.

Tant que ce fichier n'est pas rempli, les valeurs attendues de `test_calcul_are.py`
ne sont que des **tests de non-régression** — ils prouvent que le calculateur
n'a pas changé, pas qu'il est conforme à la décision France Travail réelle.

---

## Simulateur officiel

**URL** : https://candidat.francetravail.fr/candidat/simucalcul
**Version utilisée** : simulateur 2026 (règles post-réforme avril 2025)

**Conversion salaire mensuel → SJR** :
Le simulateur France Travail attend un salaire mensuel brut. `calcul_are.py`
accepte indifféremment `--salaire_mensuel` (conversion automatique) ou `--sjr`
déjà calculé. Formule : `SJR = salaire_mensuel × 12 / 365`.

---

## Cas à vérifier

Pour chaque cas : aller sur le simulateur, saisir les champs, noter l'ARE
mensuelle affichée et la durée d'indemnisation, reporter dans le tableau.
Si écart > 30 € sur le mensuel ou > 10 jours sur la durée, **bloquer le merge**
et investiguer.

### Cas 1 — SJR moyen, < 55 ans, nouveau régime

**Saisie simulateur** :
- Dernier salaire brut mensuel : `2 500 €`
- Âge à l'inscription : `35 ans`
- Durée d'affiliation (mois travaillés sur les 24 derniers) : `18 mois` (≈ 548 j)
- Motif de fin de contrat : licenciement ou rupture conventionnelle (hors démission)
- Pas d'activité réduite

**Commande équivalente** :
`python scripts/calcul_are.py --salaire_mensuel 2500 --age 35 --jours 548`

| Champ | Calcul `calcul_are.py` | Observé simulateur | Vérifié le | Écart |
|---|---|---|---|---|
| ARE journalière (€/j) | 46.85 | _____________ | __________ | ________ |
| ARE mensuelle (€) | 1 425.16 | _____________ | __________ | ________ |
| Durée indemnisation (jours) | 548 | _____________ | __________ | ________ |
| Droits totaux (€) | 25 673.42 | _____________ | __________ | ________ |

### Cas 2 — SJR élevé, plafond testé

**Saisie simulateur** :
- Dernier salaire brut mensuel : `6 000 €`
- Âge : `40 ans`
- Durée d'affiliation : `24 mois` (≈ 730 j)
- Motif : hors démission, pas d'activité réduite

**Commande équivalente** :
`python scripts/calcul_are.py --salaire_mensuel 6000 --age 40 --jours 730`

| Champ | Calcul `calcul_are.py` | Observé simulateur | Vérifié le | Écart |
|---|---|---|---|---|
| ARE journalière (€/j) | 112.44 | _____________ | __________ | ________ |
| ARE mensuelle (€) | 3 420.37 | _____________ | __________ | ________ |
| Durée indemnisation (jours) | 548 | _____________ | __________ | ________ |
| Droits totaux (€) | 61 616.22 | _____________ | __________ | ________ |

### Cas 3 — Plancher, petit salaire

**Saisie simulateur** :
- Dernier salaire brut mensuel : `1 000 €` (temps partiel)
- Âge : `28 ans`
- Durée d'affiliation : `12 mois` (≈ 365 j)

**Commande équivalente** :
`python scripts/calcul_are.py --salaire_mensuel 1000 --age 28 --jours 365`

| Champ | Calcul `calcul_are.py` | Observé simulateur | Vérifié le | Écart |
|---|---|---|---|---|
| ARE journalière (€/j) | 32.13 (plancher) | _____________ | __________ | ________ |
| ARE mensuelle (€) | 977.39 | _____________ | __________ | ________ |
| Durée indemnisation (jours) | 365 | _____________ | __________ | ________ |
| Droits totaux (€) | 11 727.45 | _____________ | __________ | ________ |

### Cas 4 — Senior 56 ans, durée étendue

**Saisie simulateur** :
- Dernier salaire brut mensuel : `3 500 €`
- Âge : `56 ans`
- Durée d'affiliation : `30 mois` (≈ 913 j, au-delà du max 685)

**Commande équivalente** :
`python scripts/calcul_are.py --salaire_mensuel 3500 --age 56 --jours 913`

| Champ | Calcul `calcul_are.py` | Observé simulateur | Vérifié le | Écart |
|---|---|---|---|---|
| ARE journalière (€/j) | 65.59 | _____________ | __________ | ________ |
| ARE mensuelle (€) | 1 995.22 | _____________ | __________ | ________ |
| Durée indemnisation (jours) | 685 | _____________ | __________ | ________ |
| Droits totaux (€) | 44 928.49 | _____________ | __________ | ________ |

### Cas 5 — Cumul ARE + activité réduite

**Saisie simulateur** :
- Dernier salaire brut mensuel : `2 400 €`
- Âge : `42 ans`
- Durée d'affiliation : `18 mois`
- Activité réduite en cours : `800 € brut / mois`

**Commande équivalente** :
`python scripts/calcul_are.py --salaire_mensuel 2400 --age 42 --jours 548 --cumul 800`

| Champ | Calcul `calcul_are.py` | Observé simulateur | Vérifié le | Écart |
|---|---|---|---|---|
| ARE solo journalière (€/j) | 45.06 | _____________ | __________ | ________ |
| ARE solo mensuelle (€) | 1 370.64 | _____________ | __________ | ________ |
| ARE réduite mensuelle (€) | 810.64 | _____________ | __________ | ________ |
| Total cumul (ARE réduite + activité) | 1 610.64 | _____________ | __________ | ________ |

---

## Procédure après vérification

1. Remplir les cases "Observé simulateur" et "Vérifié le" ci-dessus.
2. Calculer l'écart : `observé − calculé` (en valeur absolue).
3. Si tous les écarts ≤ 30 € sur le mensuel et ≤ 10 j sur la durée →
   **ajouter dans chaque cas de `test_calcul_are.py`** la mention
   `# Vérifié vs. simulateur France Travail le YYYY-MM-DD`.
4. Si un écart > seuil :
   - Vérifier la saisie (salaire brut vs net, mois vs jours cotisés, motif de fin).
   - Vérifier `data/rates/are_2026.json` (partie fixe, plancher, plafonds, durées).
   - Si l'écart persiste, noter la divergence ici avec hypothèse
     (dégressivité hauts revenus ? CSG/CRDS déjà déduits ? activité réduite
     calculée différemment ?).
5. Re-vérifier après chaque revalorisation **(1er juillet annuel Unédic)** ou
   après toute réforme de l'assurance chômage.

---

## Limites connues de `calcul_are.py` (divergences attendues)

- **Dégressivité hauts revenus** (CGT art. R. 5422-2-1) : pour SJR > 91.61 €/j
  (salaire > ~2 785 € net), dégressivité de 30 % après 182 jours d'indemnisation.
  Pas implémentée. Le simulateur France Travail l'applique automatiquement
  au-delà du seuil.
- **CSG/CRDS** : le simulateur affiche parfois l'ARE nette de CSG/CRDS (−6.7 %).
  `calcul_are.py` donne le brut Unédic. Noter si l'écart observé est proche
  de ce ratio — c'est l'explication.
- **Différé spécifique d'indemnisation** (indemnités de rupture conventionnelle
  au-delà du plancher légal) : non implémenté. Le simulateur peut ajouter 1 à
  75 jours de différé selon les primes perçues.
- **Intermittents, assistants maternels, marins** : régimes spéciaux non couverts.

Pour les comparaisons, saisir au simulateur **les champs minimaux** (salaire,
âge, durée, activité réduite) sans primes exceptionnelles ni rupture
conventionnelle au-delà du plancher.
