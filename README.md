<p align="center">
  <img src="logo.svg" alt="ai-bureau" width="520"/>
</p>

<p align="center">
  <code>local</code> &nbsp;·&nbsp; <code>privé</code> &nbsp;·&nbsp; <code>open-source</code>
</p>

---

**La paperasse française est conçue pour te noyer.** Impôts, URSSAF, retraite, crédit immo, PEA — chaque sujet est un labyrinthe avec son administration, son vocabulaire, ses pièges.

ai-bureau transforme [Claude Code](https://claude.ai/code) en fiscaliste, comptable, conseiller en patrimoine, spécialiste URSSAF et courtier crédit. Tu poses ta question. Tu obtiens une réponse opérationnelle, chiffrée, sourcée sur la règle officielle en vigueur. Tes données restent sur ta machine. Zéro abonnement. Zéro SaaS. Zéro fuite.

---

## 15 commandes

### Conseils

| Problème | Commande | Domaine |
|---|---|---|
| "Combien d'impôt sur le revenu cette année ?" | `tax-advisor` | IR 2026, niches, PFU, IFI |
| "Comment allouer 30 000 € sur mon PEA ?" | `wealth-advisor` | PEA, AV, PER, ETF, SCPI, crypto |
| "Cette offre de prêt à 3,8 % est-elle bonne ?" | `mortgage` | TAEG, assurance emprunteur, PTZ |
| "Combien l'URSSAF me prélève ce trimestre ?" | `urssaf` | Cotisations TNS, DSN, taux 2026 |
| "Quel ARE si je perds mon boulot demain ?" | `france-travail` | SJR, durée, ARCE, CPF |
| "Écritures comptables de ma SASU ?" | `business-accountant` | TVA, FEC, plan comptable |
| "Combien de trimestres retraite CNAV ?" | `pension` | CNAV, Agirc-Arrco, rachat, décote |
| "J'ai droit à l'APL ?" | `caf-benefits` | APL, prime d'activité, allocs |
| "Succession : abattements et frais de notaire ?" | `notary` | Donation, SCI, droits de mutation |
| "Mon contrat habitation me couvre-t-il vraiment ?" | `insurance` | Résiliation Hamon/Châtel, prévoyance |
| "Refaire ma carte grise — coût exact ?" | `admin` | ANTS, CNI, PACS, changement d'adresse |

### Configuration (optionnelle)

| Commande | Ce qu'elle fait |
|---|---|
| `setup-household` | Configure ton foyer fiscal (revenus, enfants, situation maritale) |
| `setup-company` | Configure ta société (forme juridique, rémunération, TVA) |
| `setup-wealth` | Configure ton patrimoine (PEA, AV, immo, crypto, PER) |

### Maintenance

| Commande | Ce qu'elle fait |
|---|---|
| `refresh-rates` | Met à jour tous les barèmes `data/rates/` depuis les sources officielles — à lancer une fois par an en janvier/février |

---

## Pourquoi c'est différent

**Local-first, vraiment.** `household.json`, `company.json`, `wealth.json` ne quittent jamais ta machine. Pas de serveur, pas de base de données, pas de télémétrie, pas de compte à créer.

**Calculs déterministes, pas de l'inférence.** Le TAEG d'un prêt, le montant ARE, le nombre de trimestres CNAV — ce sont des formules, pas des estimations. Les scripts dans `scripts/` calculent. Le LLM interprète et contextualise. Zéro hallucination numérique.

**Barèmes sourcés et horodatés.** Chaque taux dans `data/rates/` pointe vers sa source officielle avec l'année d'application. Quand un barème périme, le skill le signale.

---

## Démarrage en 2 étapes

**Prérequis** : [Claude Code](https://claude.ai/code) installé.

```bash
git clone https://github.com/HugoLopes45/ai-bureau
cd ai-bureau
claude
```

C'est tout. À l'ouverture de Claude Code, configure ta situation en français — chaque thème est optionnel :

| Tu veux... | Tape dans Claude Code |
|---|---|
| Configurer ton foyer fiscal (revenus, enfants, IR) | `utilise setup-household` |
| Configurer ta société (SASU, SARL, micro...) | `utilise setup-company` |
| Configurer ton patrimoine (PEA, AV, immo, crypto) | `utilise setup-wealth` |

Le skill te pose des questions simples en français et remplit le fichier tout seul. Pas de JSON à toucher.

Ensuite, pose tes questions directement :

```
Combien d'impôt sur le revenu cette année ?
Comment allouer 20 000 € sur mon PEA avec un profil modéré ?
Analyse cette offre de prêt : 280 000 €, 20 ans, 3,65 %
```

---

## Structure du projet

```
ai-bureau/
├── .claude/skills/           # 11 skills auto-découverts par Claude Code
│   ├── tax-advisor/          # IR, IFI, optimisation fiscale
│   ├── wealth-advisor/       # PEA, AV, PER, ETF, SCPI, crypto
│   ├── business-accountant/  # TVA, FEC, plan comptable
│   ├── mortgage/             # TAEG, assurance emprunteur, PTZ
│   ├── urssaf/               # cotisations TNS, DSN, taux 2026
│   ├── pension/              # CNAV, Agirc-Arrco, rachat, décote
│   ├── france-travail/       # ARE, CPF, ARCE
│   ├── caf-benefits/         # APL, prime d'activité, allocs
│   ├── notary/               # succession, donation, SCI
│   ├── insurance/            # habitation, auto, santé, prévoyance
│   └── admin/                # ANTS, CNI, PACS, carte grise
│
├── configs/                  # templates (copier → remplir → gitignorés)
├── data/rates/               # barèmes officiels 2026 (JSON sourcés)
├── scripts/                  # calculateurs déterministes
│
├── household.json            # ← tes vraies données (gitignored)
├── company.json              # ← tes vraies données (gitignored)
└── wealth.json               # ← tes vraies données (gitignored)
```

---

## ⚠️ À lire avant d'utiliser

**ai-bureau est un outil d'information généré par IA. Ce n'est pas du conseil réglementé.**

Les réponses peuvent être incorrectes, incomplètes ou obsolètes. Vérifie toujours contre la source officielle. Pour toute décision non triviale, consulte un professionnel agréé (expert-comptable, CIF/ORIAS, notaire, avocat fiscaliste, courtier IOBSP).

Cadre juridique complet, RGPD, AI Act (UE 2024/1689) : [`DISCLAIMER.md`](./DISCLAIMER.md).

---

## Licence

[Polyform Noncommercial 1.0.0](./LICENSE) — usage personnel et non-commercial libre. Toute exploitation commerciale est interdite sans accord explicite. Aucune affiliation avec un organisme public ou privé.
