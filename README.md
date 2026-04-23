<p align="center">
  <img src="banner.svg" alt="Marcel" width="520"/>
</p>

<p align="center">
  <code>local</code> &nbsp;·&nbsp; <code>privé</code> &nbsp;·&nbsp; <code>open-source</code>
</p>

---

> ### ⚠️ Avertissement — à lire avant usage
>
> Marcel est un **outil d'information généré par IA**. Ce n'est **pas** :
> - du conseil comptable (monopole des experts-comptables — art. L822-10 Code de commerce),
> - du conseil en investissement (monopole CIF/ORIAS — art. L541-1 CMF),
> - du conseil juridique (monopole avocats — art. 54 loi 71-1130),
> - du courtage crédit/assurance (IOBSP/IAS — art. L519-1 CMF),
> - un acte notarié (monopole notaires).
>
> Les réponses peuvent être **incorrectes, incomplètes ou obsolètes** même quand elles semblent précises. **Vérifie systématiquement** contre la source officielle et **consulte un professionnel agréé** pour toute décision non triviale.
>
> Cadre complet (RGPD, AI Act UE 2024/1689, licence, responsabilité) : [`DISCLAIMER.md`](./DISCLAIMER.md).

---

**La paperasse française est conçue pour te noyer.** Impôts, retraite, CAF, loyer, assurance, famille, héritage, crédit — chaque sujet est un labyrinthe avec son administration, son vocabulaire, ses pièges.

**Demande à Marcel.** Marcel transforme [Claude Code](https://claude.ai/code) en assistant administratif et financier pour Monsieur et Madame Tout-le-Monde. Tu poses ta question en français. Tu obtiens une réponse opérationnelle, chiffrée, sourcée sur la règle officielle en vigueur. Tes données restent sur ta machine. Zéro abonnement. Zéro SaaS. Zéro fuite.

---

## 19 commandes

### Point d'entrée

| Commande | Ce qu'elle fait |
|---|---|
| `bonjour` | Si tu ne sais pas quel skill invoquer — menu cliquable qui te redirige selon ton besoin |

### Questions du quotidien — 15 domaines

| Problème | Commande | Domaine |
|---|---|---|
| "Combien d'impôt sur le revenu cette année ?" | `impots` | IR 2026, décote, PFU, IFI, PER |
| "Combien de trimestres retraite CNAV ?" | `retraite` | CNAV, Agirc-Arrco, rachat, décote, réversion |
| "J'ai droit à l'APL ?" | `caf` | APL, prime d'activité, RSA, AAH, CSS |
| "Quel ARE si je perds mon boulot demain ?" | `travail` | ARE, ARCE, CPF, CDI/CDD, rupture |
| "Mon propriétaire augmente le loyer, il peut ?" | `logement` | Bail (loi 89-462), IRL, préavis, charges |
| "Cette offre de prêt à 3,8 % est-elle bonne ?" | `credit` | TAEG, usure, assurance emprunteur, PTZ |
| "Ma maison vaut combien ? Je vends ou je loue ?" | `immobilier` | DVF, LMNP, plus-value |
| "Succession : abattements et frais de notaire ?" | `notaire` | Donation, SCI, droits de mutation |
| "Mon contrat habitation me couvre-t-il vraiment ?" | `assurance` | Résiliation Hamon/Chatel, prévoyance |
| "Mariage, PACS ou divorce : quel régime ?" | `famille` | PACS, mariage (4 régimes), naissance, divorce |
| "Comment allouer 30 000 € sur mon PEA ?" | `patrimoine` | PEA, AV, PER, livret A, SCPI |
| "Refaire ma carte grise — coût exact ?" | `administratif` | ANTS, CNI, PACS, changement d'adresse |
| "Ma mutuelle me rembourse combien sur mes lunettes ?" | `sante` | Sécu, mutuelle (Hamon/ANI), CSS, ALD, 100 % santé |
| "Je me rétracte d'un achat en ligne, comment ?" | `consommation` | Rétractation 14j, garantie, résiliation, litige |
| "Décès d'un proche, quelles démarches ?" | `deces` | Obsèques, banques, réversion, AV, capital décès |

### Configuration (optionnelle) — 2 assistants

| Commande | Ce qu'elle fait |
|---|---|
| `mon-foyer` | Configure `foyer.json` (revenus, enfants, situation). Backup + diff avant écriture. |
| `mon-patrimoine` | Configure `patrimoine.json` (PEA, AV, immo, crypto, PER). Backup + diff avant écriture. |

### Maintenance

| Commande | Ce qu'elle fait |
|---|---|
| `mettre-a-jour-taux` | Scanne `data/rates/*.json`, détecte les barèmes périmés, rafraîchit depuis les sources officielles. À lancer en janvier/février annuel. |

---

## Pourquoi c'est différent

**Local-first, vraiment.** `foyer.json` et `patrimoine.json` ne quittent jamais ta machine. Pas de serveur, pas de base de données, pas de télémétrie, pas de compte à créer.

**Calculs déterministes, pas de l'inférence.** Le TAEG d'un prêt, le montant ARE, le nombre de trimestres CNAV — ce sont des formules, pas des estimations. Les scripts dans `scripts/` calculent. Le LLM interprète et contextualise. Zéro hallucination numérique.

**Barèmes sourcés et horodatés.** Chaque taux dans `data/rates/` pointe vers sa source officielle avec l'année d'application. Quand un barème périme, le skill le signale.

---

## Démarrage

**Prérequis** : [Claude Code](https://claude.ai/code).

Ouvre Claude Code, colle ce prompt et envoie :

```
Clone https://github.com/HugoLopes45/marcel localement, copie configs/foyer.example.json → foyer.json et configs/patrimoine.example.json → patrimoine.json (sans écraser si déjà présents), puis ouvre Claude Code dans ce répertoire.
```

Ensuite :

```
/bonjour
```

---

## Structure du projet

```
marcel/
├── .claude/commands/            # 19 skills — un fichier .md par skill
│   ├── bonjour.md               # point d'entrée, menu cliquable
│   ├── impots.md retraite.md caf.md travail.md
│   ├── logement.md credit.md immobilier.md notaire.md
│   ├── assurance.md famille.md patrimoine.md administratif.md
│   ├── sante.md consommation.md deces.md
│   ├── mon-foyer.md mon-patrimoine.md   # config lazy + backup/diff
│   └── mettre-a-jour-taux.md             # maintenance annuelle
│
├── scripts/                     # calculateurs déterministes (Python stdlib)
│   ├── _freshness.py            # check _meta.derniere_verification (partagé)
│   ├── calcul_ir.py             # IR 2026 (barème, QF, décote)
│   ├── calcul_are.py            # ARE Unédic + ARCE
│   ├── calcul_succession.py     # droits succession CGI art. 777-779
│   ├── calcul_taeg.py           # TAEG actuariel + check usure Banque de France
│   ├── test_calcul_*.py         # 95 tests : known + property-based bornes
│   └── golden_cases_*.md        # procédure vérif contre simulateurs officiels
│
├── configs/                     # templates foyer.example.json, patrimoine.example.json
├── data/rates/                  # 21 fichiers *_2026.json — barèmes sourcés
│                                #   avec `_meta.derniere_verification`
│
├── foyer.json                   # ← tes vraies données (gitignored)
└── patrimoine.json              # ← tes vraies données (gitignored)
```

---

## Pour les professionnels → paperasse

Marcel est conçu pour les **particuliers**. Pour les besoins professionnels (comptabilité SASU/SARL, TVA, FEC, cotisations TNS, URSSAF, facturation électronique, expert-comptable), **utilise [paperasse](https://github.com/romainsimon/paperasse)** — l'excellent projet de [Romain Simon](https://github.com/romainsimon) qui couvre le segment B2B. Architecture éprouvée, base de connaissance fiscale pro solide, parfaitement complémentaire à Marcel.

---

## ⚠️ À lire avant d'utiliser

**Marcel est un outil d'information généré par IA. Ce n'est pas du conseil réglementé.**

Les réponses peuvent être incorrectes, incomplètes ou obsolètes. Vérifie toujours contre la source officielle. Pour toute décision non triviale, consulte un professionnel agréé (expert-comptable, CIF/ORIAS, notaire, avocat fiscaliste, courtier IOBSP).

Cadre juridique complet, RGPD, AI Act (UE 2024/1689) : [`DISCLAIMER.md`](./DISCLAIMER.md).

---

## Crédits & inspiration

Marcel a été inspiré par **[paperasse](https://github.com/romainsimon/paperasse) de [Romain Simon](https://github.com/romainsimon)** — un super projet qui a ouvert la voie des skills Claude Code pour la paperasse française. L'architecture de Marcel (skills par domaine, scripts déterministes pour les chiffres, JSON sourcés pour les barèmes) reprend directement les bonnes idées de paperasse.

Les deux projets sont **complémentaires et non concurrents** :

| | paperasse | Marcel |
|---|---|---|
| **Cible** | Professionnels, freelances, experts-comptables | Particuliers, "Monsieur et Madame Tout-le-Monde" |
| **Scope** | SASU, SARL, TVA, FEC, URSSAF TNS, facturation | IR particulier, retraite, CAF, logement, famille, santé, décès… |
| **Public** | Dirigeants, entrepreneurs, comptables | Salariés, retraités, foyers fiscaux classiques |

Si tu es pro : va voir paperasse. Si tu es particulier et que tu cherches à comprendre ton IR ou tes droits CAF : reste ici.

---

## Licence

[Polyform Noncommercial 1.0.0](./LICENSE) — usage personnel et non-commercial libre. Toute exploitation commerciale est interdite sans accord explicite. Aucune affiliation avec un organisme public ou privé.
