# Golden cases — `calcul_taeg.py` vs. sources officielles

Procédure de vérification des valeurs attendues dans `test_calcul_taeg.py`.

**Important** : comme pour la succession, **il n'existe pas de simulateur
officiel unifié** pour le TAEG. La méthode légale est définie dans le
Code de la consommation art. R. 314-1 (annexe), mais la DGFiP / Banque de
France ne publie pas de calculateur en ligne. La vérification passe par :

1. **Excel / LibreOffice** : fonction `TAUX(n, -M, C)` retourne le taux
   mensuel, à passer en annuel actuariel via `(1 + taux)^12 − 1`.
2. **Simulateur ANIL** (agence d'information logement, financée par l'État) :
   https://www.anil.org/outils-calculateurs/
3. **Simulateurs privés** (Meilleurtaux, Pretto, Empruntis) — pour
   recoupement, pas pour autorité.
4. **Contrat de prêt d'une vraie banque** : le TAEG y est obligatoirement
   affiché (Code conso art. L. 314-5).

Tant que ce fichier n'est pas rempli, les valeurs attendues de
`test_calcul_taeg.py` sont des **tests de non-régression** calculés à la main
depuis la formule d'amortissement et la convention actuarielle annuelle —
pas une conformité vérifiée.

---

## Sources à utiliser

- **Code de la consommation art. L. 314-1 à L. 314-5** (TAEG, obligations) :
  https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069565/LEGISCTA000032227175
- **Code de la consommation art. R. 314-1** (méthode de calcul TAEG, annexe) :
  https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069565/LEGISCTA000032807551
- **Banque de France — Taux d'usure** (publication trimestrielle) :
  https://www.banque-france.fr/fr/statistiques/taux-et-cours/taux-dusure
- **ANIL — Simulateurs crédit logement** :
  https://www.anil.org/outils-calculateurs/
- **Loi Lemoine** (résiliation assurance emprunteur à tout moment, CCH art. L.
  313-30) : https://www.service-public.fr/particuliers/vosdroits/F73296

---

## Cas à vérifier

### Cas 1 — Immo 200 000 € / 3,00 % / 20 ans, sans assurance ni frais

**Commande** :
`python scripts/calcul_taeg.py --capital 200000 --taux 3.0 --duree 240`

**Calcul manuel** :
- `i_m = 0.03/12 = 0.0025`
- `M = 200 000 × 0.0025 / (1 − 1.0025^(−240)) = 1 109,20 €/mois`
- `TAEG = (1.0025)^12 − 1 = 3,042 %` (actuariel, > nominal 3 % car composition)

**Vérif Excel** : `=-PMT(0.0025, 240, 200000)` → 1 109,20. `=TAUX(240, -1109.20, 200000)*12` → 3,0000 % (taux mensuel × 12 = nominal). `((1+TAUX/1)^12-1)` → 3,042 % actuariel.

| Calcul `calcul_taeg.py` | Calcul manuel | ANIL / Excel | Vérifié le |
|---|---|---|---|
| mensualité 1 109,20 € | 1 109,20 € | ______ | __________ |
| TAEG 3,042 % | 3,042 % | ______ | __________ |

### Cas 2 — Immo 200 000 € / 3,00 % / 20 ans + assurance 30 €/mois

**Commande** :
`python scripts/calcul_taeg.py --capital 200000 --taux 3.0 --duree 240 --assurance 30`

**Règle** : mensualité hors assurance inchangée. TAEG monte par rapport au
cas 1 car surcoût assurance 7 200 € sur 20 ans.

| Calcul `calcul_taeg.py` | Vérif ANIL / Excel | Vérifié le |
|---|---|---|
| mensualité totale 1 139,20 € | ______ | __________ |
| TAEG ≈ 3,348 % | ______ | __________ |

### Cas 3 — Conso 5 000 € / 8,00 % / 36 mois

**Commande** :
`python scripts/calcul_taeg.py --capital 5000 --taux 8.0 --duree 36 --type conso_3000_6000`

**Calcul manuel** :
- `i_m = 0.08/12 = 0.006667`
- `M = 5 000 × 0.006667 / (1 − 1.006667^(−36)) ≈ 156,68 €/mois`
- `TAEG = (1.006667)^12 − 1 ≈ 8,300 %`
- Usure Q2 2026 pour conso 3 000–6 000 € = **15,73 %** → 8,30 % < 15,73 % OK.

| Calcul `calcul_taeg.py` | Calcul manuel | Vérifié le |
|---|---|---|
| mensualité 156,68 € | 156,68 € | __________ |
| TAEG 8,300 % | 8,300 % | __________ |

### Cas 4 — PTZ 50 000 € / 0,00 % / 25 ans

**Commande** :
`python scripts/calcul_taeg.py --capital 50000 --taux 0.0 --duree 300`

**Règle** : taux 0 → mensualité = capital / durée = 50 000 / 300 = 166,67 €.
Sans frais ni assurance, TAEG = 0 %.

| Calcul `calcul_taeg.py` | Règle | Vérifié le |
|---|---|---|
| mensualité 166,67 € | 50 000 / 300 | __________ |
| TAEG 0,000 % | trivial | __________ |

### Cas 5 — Conso 10 000 € / 10,00 % (dépasse usure)

**Commande** :
`python scripts/calcul_taeg.py --capital 10000 --taux 10.0 --duree 60 --type conso_6000_plus`

**Règle** : usure Q2 2026 pour conso > 6 000 € = 8,61 %. Avec taux nominal
10 %, TAEG ≈ 10,47 % > 8,61 % → contrat illégal.

| Calcul `calcul_taeg.py` | Règle | Vérifié le |
|---|---|---|
| TAEG ≈ 10,47 % | > 8,61 % usure | __________ |
| drapeau `usure_depasse` | `True` | __________ |

---

## Procédure après vérification

1. Pour chaque cas, ouvrir Excel / LibreOffice et calculer avec `PMT` / `TAUX`.
2. Confronter à un simulateur ANIL (outil public, gratuit).
3. Si les 5 cas passent → ajouter dans chaque cas de `test_calcul_taeg.py`
   la mention `# Vérifié vs. Excel et ANIL le YYYY-MM-DD`.
4. Si un écart > 5 centimes sur la mensualité ou > 0,05 pt sur le TAEG :
   - Vérifier la convention de calcul (actuariel annuel, pas nominal × 12).
   - Vérifier que les frais sont bien déduits du **capital net** au démarrage.
   - Vérifier `data/rates/taux_usure_2026_q2.json` (taux applicable au type).
5. Re-vérifier **à chaque trimestre** (Banque de France publie fin
   mars/juin/septembre/décembre pour le trimestre suivant).

---

## Limites connues de `calcul_taeg.py` (divergences attendues)

- **Assurance en % du capital restant dû** : certaines banques facturent
  l'assurance emprunteur proportionnellement au capital restant (qui diminue
  chaque mois). `calcul_taeg.py` modélise uniquement la prime **constante**
  (cas le plus courant en 2026, notamment avec loi Lemoine et délégation).
  Pour une assurance CRD, le TAEG calculé ici **sous-estime** légèrement le
  TAEG réel en début de prêt, le **surestime** en fin.
- **Caution Crédit Logement** (alternative à l'hypothèque) : coûte ~0,8–1,2 %
  du capital, partiellement remboursée en fin de prêt. Non modélisée ici —
  à ajouter aux `frais_dossier` en première approximation (écart TAEG
  généralement < 0,1 pt).
- **Pénalités remboursement anticipé (IRA)** : hors calcul TAEG par convention
  (Code conso art. R. 314-4-IV). N'apparaît pas dans le TAEG d'origine.
- **Période différée** (franchise partielle ou totale pendant la construction)
  : non couverte. Modifie le TAEG sensiblement.
- **Prêts à taux variable** : `immo_variable` utilise le taux nominal initial.
  Le TAEG réel dépendra des révisions futures — inconnaissable à la signature.
- **Frais de notaire** : ne sont **pas** dans le TAEG (c'est l'acquisition
  immobilière, pas le crédit). Ne pas les ajouter à `frais_dossier`.
- **Prime initiale d'assurance** : si l'assurance est payée en une fois au
  démarrage (rare), il faut l'ajouter aux `frais_dossier` et mettre
  `assurance_mensuelle=0`. Le TAEG calculé sera alors correct.

Pour une comparaison avec un simulateur tiers, choisir le profil
« assurance mensuelle constante, remboursement in fine des frais = 0,
pas de différé ».
