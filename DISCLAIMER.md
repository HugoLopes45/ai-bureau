# Avertissement — À lire avant d'utiliser ai-bureau

## 1. Ce que ai-bureau est

Un ensemble de skills Claude Code qui aident à comprendre, estimer et structurer des démarches administratives, fiscales, sociales et patrimoniales françaises. **Tout est généré par une intelligence artificielle.**

## 2. Ce que ai-bureau n'est pas

- ❌ Une prestation de **conseil comptable** — article L822-10 du Code de commerce (monopole des experts-comptables inscrits à l'Ordre).
- ❌ Une prestation de **conseil en investissement financier (CIF)** — règlement général AMF + inscription ORIAS requises pour toute recommandation personnalisée (articles L541-1 et suivants du CMF).
- ❌ Une prestation de **conseil juridique** — article 54 de la loi n°71-1130 (monopole des avocats et professions réglementées).
- ❌ Une prestation de **courtage** en opérations de banque ou en assurance (IOBSP / IAS — inscription ORIAS obligatoire, articles L519-1 et L511-1 du CMF).
- ❌ Un acte notarié ou un conseil notarial (monopole des notaires, ordonnance n°45-2590).

**ai-bureau ne remplace aucun de ces professionnels.**

---

## 3. Données personnelles et confidentialité

### 3.1 Aucune rétention par ai-bureau

ai-bureau est un projet local, **sans serveur, sans base de données, sans télémétrie, sans logs**. Les fichiers `household.json`, `company.json`, `wealth.json` et tout document inséré par l'utilisateur restent **exclusivement sur sa machine**. Les auteurs et contributeurs de ai-bureau n'ont **aucun accès** à ces données et ne collectent absolument rien.

### 3.2 Flux de données vers le fournisseur d'IA

Quand l'utilisateur invoque un skill, le contenu de la conversation et les données nécessaires à la réponse sont transmis au fournisseur du modèle d'IA utilisé (par défaut **Anthropic** via Claude Code). Ce transfert est **hors du contrôle d'ai-bureau**.

**Il est de la responsabilité de l'utilisateur** de lire et comprendre :
- La politique de confidentialité d'Anthropic : <https://www.anthropic.com/legal/privacy>
- La politique de rétention des données de Claude Code
- Les conditions d'utilisation du plan souscrit (gratuit, Pro, Team, API)

Pour ne pas envoyer de données sensibles au modèle : ne remplis pas les fichiers `*.json` ou utilise des valeurs fictives.

### 3.3 Droits RGPD (Règlement UE 2016/679)

En tant qu'utilisateur résident UE, tu disposes des droits d'accès, de rectification, d'effacement, d'opposition, de limitation et de portabilité sur tes données personnelles.

- **Auprès d'ai-bureau** : rien à demander, puisque nous ne détenons rien.
- **Auprès d'Anthropic** (fournisseur de l'IA) : voir sa politique de confidentialité et les procédures qu'elle décrit.
- **Auprès des administrations françaises** (impôts, URSSAF, CAF, etc.) : les procédures RGPD sont décrites sur [cnil.fr](https://www.cnil.fr).

Autorité de contrôle compétente en France : **CNIL** — <https://www.cnil.fr>.

### 3.4 Données de tiers

Ne saisis dans ai-bureau que des données **dont tu es le responsable** (les tiennes, ou celles pour lesquelles tu as une base légale de traitement). Insérer les données personnelles d'un tiers sans son consentement ou sans base légale constitue un manquement au RGPD, dont tu es seul responsable.

---

## 4. Règlement IA européen (AI Act — Règlement UE 2024/1689)

ai-bureau utilise un système d'IA générative (LLM d'Anthropic). Conformément à l'article 50 du Règlement IA :

- **Tu es informé(e) que tu interagis avec un système d'IA.** Les skills le rappellent à la fin de chaque réponse substantielle.
- ai-bureau ne constitue pas un **système d'IA à haut risque** au sens de l'annexe III du Règlement — il n'intervient pas dans l'éducation, l'emploi, les services essentiels publics ou privés, la gestion des migrations, l'administration de la justice, ni les processus démocratiques, en tant que système décisionnel.
- L'usage reste à titre **informatif et éducatif**. Aucune décision automatisée au sens de l'article 22 RGPD n'est prise à l'encontre de l'utilisateur.

---

## 5. Fiabilité et vérification

1. **Les réponses sont générées par une IA.** Elles peuvent être incorrectes, incomplètes, obsolètes ou inadaptées — même quand elles semblent précises et chiffrées.

2. **Les barèmes et règles évoluent.** Un taux correct au moment de la rédaction peut avoir changé depuis. La date de dernière mise à jour figure dans chaque skill (`last_updated`) et dans `data/rates/*.json`.

3. **Vérifie systématiquement** un résultat avant toute action, contre la source officielle :

| Domaine | Source officielle |
|---|---|
| Fiscalité | [impots.gouv.fr](https://www.impots.gouv.fr) |
| Cotisations sociales | [urssaf.fr](https://www.urssaf.fr) |
| Droits et démarches | [service-public.fr](https://www.service-public.fr) |
| Textes de loi | [legifrance.gouv.fr](https://www.legifrance.gouv.fr) |
| Taux d'usure, statistiques bancaires | [banque-france.fr](https://www.banque-france.fr) |
| Retraite | [info-retraite.fr](https://www.info-retraite.fr) |
| France Travail / Unédic | [francetravail.fr](https://www.francetravail.fr), [unedic.org](https://www.unedic.org) |
| CAF | [caf.fr](https://www.caf.fr) |
| CNIL / données personnelles | [cnil.fr](https://www.cnil.fr) |

---

## 6. Quel professionnel consulter

Pour toute décision non triviale (montants significatifs, structuration fiscale, contentieux, succession, contrat, investissement important) :

| Domaine | Professionnel agréé |
|---|---|
| Comptabilité, bilan, liasse, choix de régime | **Expert-comptable** (Ordre des experts-comptables) |
| Investissements, allocation patrimoniale, assurance-vie | **CIF / CGPA agréé** (registre ORIAS) |
| Crédit immobilier ou à la consommation | **Courtier IOBSP** (registre ORIAS) |
| Immobilier, famille, succession, donation | **Notaire** (Notaires de France) |
| Contentieux fiscal, montages complexes | **Avocat fiscaliste** |
| Droit social, prud'hommes, contrat de travail | **Avocat en droit social** |
| Contentieux URSSAF / sécurité sociale | **Avocat** ou défenseur syndical |

---

## 7. Portée territoriale

ai-bureau cite les règles françaises applicables aux **résidents fiscaux français** et aux **entreprises établies en France**. Il n'est pas adapté :
- aux non-résidents,
- aux conventions fiscales internationales,
- aux situations transfrontalières (pluri-résidents, expats, travailleurs détachés),
- aux régimes spécifiques (Alsace-Moselle, DROM-COM, Monaco, TOM).

Pour ces cas → consulte un professionnel spécialisé (avocat fiscaliste international, notaire maîtrisant le droit international privé).

---

## 8. Responsabilité

**L'utilisateur est seul responsable** de ses décisions et de la vérification des informations avant toute action.

Les auteurs, contributeurs, mainteneurs et utilisateurs d'ai-bureau, ainsi que le modèle d'IA sous-jacent, **déclinent toute responsabilité** liée à l'usage des réponses produites, directement ou indirectement :
- Erreurs de calcul ou d'interprétation
- Obsolescence d'un barème, seuil ou règle
- Mauvaise prise en compte du contexte individuel
- Conséquences fiscales, sociales, financières ou juridiques d'une décision fondée sur une réponse
- Perte de chance, perte de droits, redressement, pénalité

Aucune garantie explicite ou implicite n'est donnée (ni de précision, ni d'exhaustivité, ni d'actualité, ni d'adéquation à un usage particulier).

Ce projet est distribué sous licence **MIT** (voir `LICENSE`). Tout usage vaut acceptation sans réserve des termes du présent avertissement et de la licence.

---

## 9. Signalement

Si un skill produit une réponse manifestement fausse, obsolète ou dangereuse, corrige la source (`data/rates/*.json`, `data/sources.md`, ou la `SKILL.md` concernée) et partage la correction.

Pour toute question RGPD concernant les données transmises au fournisseur d'IA : contacte directement **Anthropic** via sa politique de confidentialité.

Pour une plainte relative à la protection des données personnelles : **CNIL** — <https://www.cnil.fr/fr/plaintes>.
