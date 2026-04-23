# Golden cases — `calcul_succession.py` vs. sources officielles

Procédure de vérification des valeurs attendues dans `test_calcul_succession.py`.

**Important** : contrairement à l'IR (simulateur-ir.impots.gouv.fr) et l'ARE
(simucalcul France Travail), **il n'existe pas de simulateur officiel unifié
pour les droits de succession**. La DGFiP ne publie pas de calculateur en ligne.
La vérification passe par :

1. Les **exemples chiffrés** sur impots.gouv.fr (rares mais précis).
2. Le **calcul manuel** depuis CGI art. 777 et 779 (barème + abattement).
3. **OpenFisca-France** — module `successions` (tests unitaires en Python).
4. Un notaire pour une succession réelle (tarif consultation ~150 €).

Tant que ce fichier n'est pas rempli, les valeurs attendues de
`test_calcul_succession.py` sont des **tests de non-régression**, calculés à la
main depuis le barème DGFiP — pas une conformité vérifiée contre une source
d'autorité.

---

## Sources à utiliser

- **impots.gouv.fr — Comment calculer les droits de succession** :
  https://www.impots.gouv.fr/particulier/questions/comment-dois-je-calculer-les-droits-de-succession
- **Service-Public F14199 — Droits de succession** :
  https://www.service-public.fr/particuliers/vosdroits/F14199
- **BOFiP — BOI-ENR-DMTG-10** (doctrine administrative) :
  https://bofip.impots.gouv.fr/bofip/2782-PGP.html
- **CGI art. 777** (barème) :
  https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000044989768
- **CGI art. 779** (abattements) :
  https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000044989786
- **OpenFisca-France** (dernière version) :
  https://github.com/openfisca/openfisca-france
  (chercher `tests/formulas/succession` ou `parameters/taxation/prelevements_sociaux`)

---

## Cas à vérifier

Pour chaque cas, **refaire le calcul à la main** depuis le barème, et/ou
chercher un exemple équivalent sur impots.gouv.fr. Si divergence > 2 € → bug.

### Cas 1 — Enfant reçoit 300 000 € (cas standard, tranche 20 %)

**Commande** :
`python scripts/calcul_succession.py --actif 300000 --lien enfant`

**Calcul manuel (CGI art. 777, 779)** :
- Abattement enfant = 100 000 € (art. 779 I)
- Base taxable = 300 000 − 100 000 = 200 000 €
- Barème ligne directe :
  - 0 → 8 072 × 5 %   = 403,60 €
  - 8 072 → 12 109 × 10 %   = 403,70 €
  - 12 109 → 15 932 × 15 %   = 573,45 €
  - 15 932 → 200 000 × 20 %  = 36 813,60 €
- **Total = 38 194,35 €**

| Calcul `calcul_succession.py` | Calcul manuel | Vérifié le | Source |
|---|---|---|---|
| 38 194 € | 38 194,35 € | __________ | __________ |

### Cas 2 — Conjoint reçoit 1 000 000 € (exonération totale)

**Commande** :
`python scripts/calcul_succession.py --actif 1000000 --lien conjoint`

**Règle (CGI art. 796-0 bis, loi TEPA 21/08/2007)** :
Le conjoint survivant ou partenaire de PACS est **totalement exonéré** de
droits de succession, quel que soit le montant reçu.

| Calcul `calcul_succession.py` | Règle | Vérifié le | Source |
|---|---|---|---|
| 0 € | exonération totale | __________ | impots.gouv.fr |

### Cas 3 — Frère/sœur reçoit 50 000 €

**Commande** :
`python scripts/calcul_succession.py --actif 50000 --lien frere_soeur`

**Calcul manuel** :
- Abattement frère/sœur = 15 932 € (CGI art. 779 IV)
- Base taxable = 50 000 − 15 932 = 34 068 €
- Barème frère/sœur (CGI art. 777) :
  - 0 → 24 430 × 35 % = 8 550,50 €
  - 24 430 → 34 068 × 45 % = 4 337,10 €
- **Total = 12 887,60 €**

| Calcul `calcul_succession.py` | Calcul manuel | Vérifié le | Source |
|---|---|---|---|
| 12 888 € | 12 887,60 € | __________ | __________ |

### Cas 4 — Non-parent reçoit 100 000 € (concubin, ami)

**Commande** :
`python scripts/calcul_succession.py --actif 100000 --lien non_parent`

**Calcul manuel** :
- Abattement résiduel = 1 594 € (CGI art. 788 IV)
- Base taxable = 100 000 − 1 594 = 98 406 €
- Taux forfaitaire non-parent = 60 % (CGI art. 777)
- **Total = 98 406 × 0,60 = 59 043,60 €**

| Calcul `calcul_succession.py` | Calcul manuel | Vérifié le | Source |
|---|---|---|---|
| 59 044 € | 59 043,60 € | __________ | __________ |

### Cas 5 — Enfant handicapé reçoit 300 000 € (cumul abattement)

**Commande** :
`python scripts/calcul_succession.py --actif 300000 --lien enfant --handicape`

**Calcul manuel (CGI art. 779 II — abattement cumulable)** :
- Abattement de base = 100 000 €
- Abattement handicapé = +159 325 €
- Abattement total = 259 325 €
- Base taxable = 300 000 − 259 325 = 40 675 €
- Barème ligne directe :
  - 0 → 8 072 × 5 %   = 403,60 €
  - 8 072 → 12 109 × 10 % = 403,70 €
  - 12 109 → 15 932 × 15 % = 573,45 €
  - 15 932 → 40 675 × 20 % = 4 948,60 €
- **Total = 6 329,35 €**

| Calcul `calcul_succession.py` | Calcul manuel | Vérifié le | Source |
|---|---|---|---|
| 6 329 € | 6 329,35 € | __________ | __________ |

---

## Procédure après vérification

1. Pour chaque cas, **refaire le calcul à la main** (barème tranche par tranche).
2. Chercher un exemple équivalent sur impots.gouv.fr / service-public.fr /
   openfisca-france.
3. Si les 5 cas passent → **ajouter dans chaque cas de
   `test_calcul_succession.py`** la mention
   `# Vérifié vs. calcul manuel CGI art. 777-779 le YYYY-MM-DD`.
4. Si un écart > 2 € :
   - Vérifier `data/rates/succession_dons_2026.json` (abattements, barèmes).
   - Vérifier le mapping `lien_parente → abattement` dans `calcul_succession.py`
     (piège déjà corrigé : ne pas laisser "non-parents" matcher "4ème degré"
     en premier dans le parsing JSON).
   - Ouvrir une issue avec le cas + calcul attendu.
5. Re-vérifier après chaque loi de finances (janvier de chaque année). Les
   abattements art. 779 et le barème art. 777 sont stables depuis 2012 — toute
   modification sera une nouvelle politique fiscale.

---

## Limites connues de `calcul_succession.py` (divergences attendues)

- **Démembrement de propriété** (CGI art. 669) : usufruit/nue-propriété non
  calculés. Si l'héritier reçoit la nue-propriété, sa valeur fiscale est une
  fraction de la pleine propriété (selon âge de l'usufruitier). Non implémenté.
- **Assurance-vie** : **hors succession** (art. L132-12 Code des assurances +
  CGI art. 990 I pour versements avant 70 ans, art. 757 B après). Abattement
  152 500 € par bénéficiaire avant 70 ans. Non calculé ici.
- **Pacte Dutreil** (CGI art. 787 B) : abattement 75 % sur la transmission
  d'une entreprise sous conditions d'engagement collectif. Non calculé.
- **Dons spéciaux** :
  - **Don familial d'argent** (CGI art. 790 G) : +31 865 € cumulable, conditions
    d'âge (donateur < 80 ans, bénéficiaire majeur). Non calculé.
  - **Don logement temporaire** (LF 2025, art. 790 A) : jusqu'à 100 000 €/donateur
    en exonération totale jusqu'au 31/12/2026, affectation résidence principale
    ou rénovation énergétique. Non calculé.
- **Réduction art. 780 CGI** (charges de famille) : 305 € par enfant à charge
  au-delà du 2e (610 € en ligne directe). Marginale, non implémentée.
- **Réduction art. 790 CGI** (âge du donateur < 70 ans) : réduction 50 % des
  droits de donation (pas succession). Non applicable ici (scope succession).
- **Exonération frère/sœur spéciale** (CGI art. 796-0 ter) : célibataire/veuf,
  vivant avec le défunt depuis 5 ans, > 50 ans ou invalide — exonération
  totale. Non implémentée (cas rare, nécessite des preuves de vie commune).
- **Partage civil de l'actif** : le script prend **actif reçu par UN héritier**
  en entrée. Le partage entre cohéritiers (réserves héréditaires, quotité
  disponible, rapport des donations antérieures) relève du droit civil et du
  notaire, pas du fiscal.

Pour les comparaisons, utiliser des **cas simples** (un seul héritier, pas
d'assurance-vie, pas de démembrement, pas de don Dutreil).
