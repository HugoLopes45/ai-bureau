#!/usr/bin/env python3
"""
calcul_are.py — Calculateur ARE 2026 — Marcel

Usage:
    python scripts/calcul_are.py --sjr 80 --age 42 --jours 365
    python scripts/calcul_are.py --salaire_mensuel 2500 --age 50 --jours 548
    python scripts/calcul_are.py --sjr 120 --age 45 --jours 400 --cumul 900
    python scripts/calcul_are.py --sjr 95 --age 38 --jours 300 --droits_restants 200 --json
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _freshness import check_freshness

ROOT = Path(__file__).parent.parent
RATES_ARE = ROOT / "data" / "rates" / "are_2026.json"
RATES_ARCE = ROOT / "data" / "rates" / "arce_2026.json"

# Coupure réforme avril 2025 — détermine le plafond applicable
DATE_REFORME = date(2025, 4, 1)


def _charger_parametres():
    """
    Charge les paramètres ARE et ARCE depuis les fichiers de taux.

    Sources (via are_2026.json et arce_2026.json) :
      - ARE : Code du travail art. L. 5422-1 et s., règlement général Unédic
        annexé à la convention d'assurance chômage du 15/11/2023
      - Réforme plafond 75 % → 70 % : décret n° 2025-xxx applicable au 01/04/2025
      - Coefficient contra-cyclique (−25 % sur durée) : actif depuis 01/02/2023,
        tant que le taux de chômage reste < 9 % (arrêté trimestriel)
      - ARCE : Code du travail art. R. 5422-2, versement de 60 % des droits
    """
    with open(RATES_ARE, encoding="utf-8") as f:
        are_data = json.load(f)
    with open(RATES_ARCE, encoding="utf-8") as f:
        arce_data = json.load(f)

    check_freshness(are_data, "are_2026.json")
    check_freshness(arce_data, "arce_2026.json")

    params = {
        "partie_fixe": None,
        "plancher_journalier": None,
        "plafond_ancien": None,  # 75% — contrats fin avant avril 2025
        "plafond_nouveau": None,  # 70% — contrats fin depuis avril 2025
        "coeff_reduction_duree": None,
        "duree_max_moins_55": None,
        "duree_max_55_56": None,
        "duree_max_57_plus": None,
        "delai_attente": None,
        "arce_pct": None,
    }

    for item in are_data["donnees"]:
        label = item["item"]
        val = item["value"]
        if "partie fixe" in label:
            params["partie_fixe"] = float(val)
        elif "plancher" in label:
            params["plancher_journalier"] = float(val)
        elif "plafond" in label and "avant" in label:
            params["plafond_ancien"] = float(val) / 100
        elif "plafond" in label and "depuis" in label:
            params["plafond_nouveau"] = float(val) / 100
        elif "coefficient contra" in label:
            params["coeff_reduction_duree"] = float(val) / 100
        elif "durée maximale < 55" in label:
            params["duree_max_moins_55"] = int(val)
        elif "durée maximale 55" in label:
            params["duree_max_55_56"] = int(val)
        elif "durée maximale ≥ 57" in label:
            params["duree_max_57_plus"] = int(val)
        elif "délai d'attente" in label:
            params["delai_attente"] = int(val)

    for item in arce_data["donnees"]:
        if "pourcentage" in item["item"]:
            params["arce_pct"] = float(item["value"]) / 100

    # Garde-fou : détecter un drift de libellé JSON qui laisserait une valeur
    # silencieusement manquante → TypeError au milieu du calcul sinon.
    manquants = [k for k, v in params.items() if v is None]
    if manquants:
        raise ValueError(
            f"ARE/ARCE 2026.json : valeurs manquantes après parsing : {manquants}. "
            f"Vérifie les libellés correspondants dans data/rates/."
        )

    return params


def _duree_max(age: int, params: dict) -> int:
    """Durée maximale d'indemnisation selon l'âge (coefficient contra-cyclique déjà appliqué)."""
    if age < 55:
        return params["duree_max_moins_55"]
    elif age <= 56:
        return params["duree_max_55_56"]
    else:
        return params["duree_max_57_plus"]


def calcul_are(
    sjr: float,
    age: int,
    jours_travailles: int,
    fin_contrat_avant_reforme: bool = False,
    cumul_activite_reduite: float = 0.0,
    droits_restants: int | None = None,
) -> dict:
    """
    Calcule l'ARE journalière, mensuelle, durée et ARCE optionnelle.

    Étapes, dans l'ordre légal (Code du travail art. L. 5422-1 et règlement Unédic) :
      1. ARE brute = max(40.4 % × SJR + partie_fixe, 57 % × SJR)
      2. Plafonnement : ARE ≤ 70 % × SJR (ou 75 % si fin contrat < 01/04/2025)
      3. Plancher : ARE ≥ 32.13 €/j (sauf cumul activité réduite)
      4. Durée : min(jours_travaillés, durée_max selon âge + coeff contra-cyclique)
      5. Cumul activité réduite : ARE payable = ARE théorique − 70 % × revenu activité
      6. ARCE (option) : 60 % × droits_restants × ARE/j, versé en 2 tranches

    Hors scope de ce calculateur :
      - Dégressivité des hauts revenus (si SJR > 91,61 €/j, dégressivité à 30 %
        après 182 jours — CGT art. R. 5422-2-1)
      - Allongement de la durée de référence pour les intermittents, artistes, etc.
      - Cotisations CSG/CRDS sur l'ARE (prélevées à la source par France Travail)

    Args:
        sjr: Salaire Journalier de Référence brut (€/jour)
        age: Âge du demandeur à la date d'inscription
        jours_travailles: Jours cotisés dans la période de référence
        fin_contrat_avant_reforme: True si le contrat s'est terminé avant le 01/04/2025
        cumul_activite_reduite: Revenu brut mensuel d'une activité réduite (0 si aucune)
        droits_restants: Jours ARE restants (pour le calcul ARCE ; None = non demandé)

    Returns:
        Dict avec toutes les étapes intermédiaires pour audit humain.
    """
    if sjr < 0 or age < 0 or jours_travailles < 0 or cumul_activite_reduite < 0:
        raise ValueError(
            f"paramètres négatifs interdits : sjr={sjr}, age={age}, "
            f"jours_travailles={jours_travailles}, cumul={cumul_activite_reduite}"
        )
    if droits_restants is not None and droits_restants < 0:
        raise ValueError(f"droits_restants négatif interdit ({droits_restants})")

    params = _charger_parametres()

    # Plafond applicable selon la date de fin de contrat
    plafond_pct = params["plafond_ancien"] if fin_contrat_avant_reforme else params["plafond_nouveau"]

    # --- Étape 1 : ARE brute ---
    are_formule_a = 0.404 * sjr + params["partie_fixe"]
    are_formule_b = 0.57 * sjr
    are_brute = max(are_formule_a, are_formule_b)

    # --- Étape 2 : Plafonnement ---
    are_plafonnee = min(are_brute, plafond_pct * sjr)

    # --- Étape 3 : Plancher ---
    # Le plancher ne s'applique qu'en l'absence d'activité réduite simultanée
    are_nette = max(are_plafonnee, params["plancher_journalier"]) if cumul_activite_reduite == 0 else are_plafonnee
    are_mensuelle = round(are_nette * 30.42, 2)

    # --- Étape 4 : Durée ---
    duree_max = _duree_max(age, params)
    # La durée d'indemnisation ne peut pas dépasser les jours travaillés (plafonnée à durée_max)
    duree_indemnisation = min(jours_travailles, duree_max)

    # --- Étape 5 : Montant total des droits ---
    droits_totaux = round(are_nette * duree_indemnisation, 2)

    # --- Étape 6 : Cumul activité réduite ---
    are_cumul = None
    if cumul_activite_reduite > 0:
        # ARE payable = ARE théorique - 70% du revenu brut mensuel d'activité réduite
        are_cumul_journalier = max(0.0, are_nette - 0.70 * (cumul_activite_reduite / 30.42))
        are_cumul_mensuel = round(are_cumul_journalier * 30.42, 2)
        are_cumul = {
            "revenu_brut_mensuel": cumul_activite_reduite,
            "are_journaliere_reduite": round(are_cumul_journalier, 2),
            "are_mensuelle_reduite": are_cumul_mensuel,
        }

    # --- Étape 7 : ARCE (si demandée) ---
    arce = None
    if droits_restants is not None and droits_restants > 0:
        capital_total = round(params["arce_pct"] * droits_restants * are_nette, 2)
        arce = {
            "droits_restants_jours": droits_restants,
            "capital_total": capital_total,
            "versement_1": round(capital_total / 2, 2),
            "versement_2": round(capital_total / 2, 2),
            "are_mensuelle_maintien": are_mensuelle,
            "avantage_arce_vs_maintien": round(capital_total - are_mensuelle * (droits_restants / 30.42), 2),
        }

    return {
        "sjr": round(sjr, 2),
        "age": age,
        "jours_travailles": jours_travailles,
        "fin_contrat_avant_reforme": fin_contrat_avant_reforme,
        "plafond_pct": round(plafond_pct * 100, 0),
        "are_formule_a": round(are_formule_a, 2),
        "are_formule_b": round(are_formule_b, 2),
        "are_brute": round(are_brute, 2),
        "are_plafonnee": round(are_plafonnee, 2),
        "are_nette_journaliere": round(are_nette, 2),
        "are_nette_mensuelle": are_mensuelle,
        "duree_max_jours": duree_max,
        "duree_indemnisation_jours": duree_indemnisation,
        "droits_totaux": droits_totaux,
        "delai_attente_jours": params["delai_attente"],
        "cumul_activite_reduite": are_cumul,
        "arce": arce,
        "annee": 2026,
        "source": "data/rates/are_2026.json",
    }


def _afficher(result: dict) -> None:
    """Affiche le résultat sous forme de tableau lisible."""
    sep = "─" * 58

    print()
    titre = "ALLOCATION DE RETOUR À L'EMPLOI (ARE) 2026"
    print(f"  {titre:^54}")
    print()
    print(f"  {'Salaire journalier de référence (SJR)':<40} {result['sjr']:>9,.2f} €/j")
    print(f"  {'Âge':<40} {result['age']:>9} ans")
    print(f"  {'Jours travaillés (période de référence)':<40} {result['jours_travailles']:>9} j")
    regime = "avant avril 2025" if result["fin_contrat_avant_reforme"] else "depuis avril 2025"
    print(f"  {'Fin de contrat':<40} {regime:>9}")
    print()

    print(f"  Formule de calcul :")
    print(f"    40,4 % × SJR + partie fixe   = {result['are_formule_a']:>10,.2f} €/j")
    print(f"    57 % × SJR                   = {result['are_formule_b']:>10,.2f} €/j")
    print(f"    Maximum retenu               = {result['are_brute']:>10,.2f} €/j")
    if result["are_plafonnee"] < result["are_brute"]:
        print(f"    Plafond {result['plafond_pct']:.0f} % × SJR             = {result['are_plafonnee']:>10,.2f} €/j")
    print()
    print(f"  {sep}")
    print(f"  {'ARE NETTE JOURNALIÈRE':<40} {result['are_nette_journaliere']:>9,.2f} €/j")
    print(f"  {'ARE NETTE MENSUELLE (× 30,42)':<40} {result['are_nette_mensuelle']:>9,.2f} €/m")
    print(f"  {sep}")

    print()
    print(f"  Durée d'indemnisation :")
    print(f"    Durée max (âge {result['age']} ans, règle 2026) = {result['duree_max_jours']:>5} jours")
    print(f"    Jours travaillés cotisés      = {result['jours_travailles']:>5} jours")
    print(f"    Durée retenue                 = {result['duree_indemnisation_jours']:>5} jours")
    print(f"    Droits totaux estimés         = {result['droits_totaux']:>10,.0f} €")
    print(f"    Délai d'attente               = {result['delai_attente_jours']:>5} jours")

    if result["cumul_activite_reduite"]:
        c = result["cumul_activite_reduite"]
        print()
        print(f"  Cumul avec activité réduite ({c['revenu_brut_mensuel']:,.0f} €/mois brut) :")
        print(f"    ARE réduite journalière       = {c['are_journaliere_reduite']:>10,.2f} €/j")
        print(f"    ARE réduite mensuelle         = {c['are_mensuelle_reduite']:>10,.2f} €/m")

    if result["arce"]:
        a = result["arce"]
        print()
        print(f"  ARCE (capital création d'entreprise) :")
        print(f"    Droits restants               = {a['droits_restants_jours']:>5} jours")
        print(f"    Capital total (60 %)          = {a['capital_total']:>10,.0f} €")
        print(f"    Versement 1 (au démarrage)    = {a['versement_1']:>10,.0f} €")
        print(f"    Versement 2 (à 6 mois)        = {a['versement_2']:>10,.0f} €")
        print()
        print(f"  ARCE vs maintien mensuel :")
        print(f"    Maintien mensuel              = {a['are_mensuelle_maintien']:>10,.2f} €/m")
        print(f"    Coût d'opportunité ARCE       = {a['avantage_arce_vs_maintien']:>+10,.0f} €")
        avantage = "ARCE plus avantageux" if a["avantage_arce_vs_maintien"] > 0 else "Maintien mensuel plus avantageux"
        print(f"    → {avantage}")

    print()
    print(f"  ⚠️  Je suis une IA. Ces chiffres sont indicatifs.")
    print(f"  Vérifie sur candidat.francetravail.fr/simucalcul avec ton espace personnel.")
    print(f"  Dossier ou recours : conseiller France Travail (3949) ou avocat droit social.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcul ARE 2026 — Marcel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python scripts/calcul_are.py --sjr 80 --age 42 --jours 365
  python scripts/calcul_are.py --salaire_mensuel 2500 --age 50 --jours 548
  python scripts/calcul_are.py --sjr 120 --age 45 --jours 400 --cumul 900
  python scripts/calcul_are.py --sjr 95 --age 38 --jours 300 --droits_restants 200
""",
    )

    sjr_grp = parser.add_mutually_exclusive_group(required=True)
    sjr_grp.add_argument("--sjr", type=float, metavar="MONTANT",
                         help="SJR brut en €/jour (déjà calculé)")
    sjr_grp.add_argument("--salaire_mensuel", type=float, metavar="MONTANT",
                         help="Salaire mensuel brut → SJR = salaire × 12 / 365")

    parser.add_argument("--age", type=int, required=True,
                        help="Âge à la date d'inscription (détermine la durée max)")
    parser.add_argument("--jours", type=int, required=True, dest="jours_travailles",
                        help="Jours travaillés dans la période de référence")
    parser.add_argument("--ancien_regime", action="store_true",
                        help="Fin de contrat avant le 01/04/2025 (plafond 75%% au lieu de 70%%)")
    parser.add_argument("--cumul", type=float, default=0.0, metavar="MONTANT",
                        help="Revenu brut mensuel d'une activité réduite (calcul cumul)")
    parser.add_argument("--droits_restants", type=int, metavar="JOURS",
                        help="Jours ARE restants pour le calcul ARCE vs maintien")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Sortie JSON structurée")

    args = parser.parse_args()

    try:
        _charger_parametres()
    except FileNotFoundError as e:
        print(f"Erreur : fichier de taux introuvable — {e}", file=sys.stderr)
        sys.exit(1)

    sjr = args.sjr if args.sjr is not None else args.salaire_mensuel * 12 / 365

    result = calcul_are(
        sjr=sjr,
        age=args.age,
        jours_travailles=args.jours_travailles,
        fin_contrat_avant_reforme=args.ancien_regime,
        cumul_activite_reduite=args.cumul,
        droits_restants=args.droits_restants,
    )

    if args.json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _afficher(result)


if __name__ == "__main__":
    main()
