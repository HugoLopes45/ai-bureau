#!/usr/bin/env python3
"""
calcul_ir.py — Calculateur IR 2026 (revenus 2025) — Marcel

Usage:
    python scripts/calcul_ir.py --rni 45000 --parts 1
    python scripts/calcul_ir.py --rni 80000 --parts 2.5 --situation couple
    python scripts/calcul_ir.py --foyer foyer.json
    python scripts/calcul_ir.py --rni 45000 --parts 1 --json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _freshness import check_freshness

ROOT = Path(__file__).parent.parent
RATES_FILE = ROOT / "data" / "rates" / "ir_2026.json"

# Coefficient décote (fixe, non indexé — CGI art. 197-I-4)
COEFF_DECOTE = 0.4525


def _load_bareme():
    """
    Charge le barème IR et les paramètres de décote depuis le fichier de taux.

    Sources (via ir_2026.json) :
      - Barème progressif : CGI art. 197-I, loi n° 2026-103 du 19 février 2026 art. 4
      - Quotient familial : CGI art. 194 (parts), art. 197-I-2 (plafond demi-part)
      - Décote : CGI art. 197-I-4 (coefficient 0.4525 reconduit pour 2026)
    """
    with open(RATES_FILE, encoding="utf-8") as f:
        data = json.load(f)

    check_freshness(data, "ir_2026.json")

    tranches = []
    decote = {}
    quotient_familial = {}

    for item in data["donnees"]:
        label = item["item"]
        val = item["value"]

        if "barème progressif" in label and isinstance(val, dict) and "rate" in val:
            tranches.append({
                "min": val["min"],
                "max": val["max"],  # None pour la dernière tranche
                "rate": val["rate"],
            })
        elif "décote" in label and "célibataire" in label:
            decote["celibataire"] = val
        elif "décote" in label and "couple" in label:
            decote["couple"] = val
        elif "quotient familial" in label and "plafond" in label:
            quotient_familial["plafond_demi_part"] = val  # en € par demi-part supplémentaire

    tranches.sort(key=lambda t: t["min"])

    # Garde-fou : détecter un drift de libellé JSON (renommage) qui laisserait
    # des valeurs silencieusement manquantes. Meilleur d'échouer fort au boot
    # que de cracher un TypeError au milieu du calcul.
    if len(tranches) != 5:
        raise ValueError(
            f"ir_2026.json : {len(tranches)} tranches chargées (5 attendues). "
            f"Les libellés 'barème progressif' ont-ils été renommés ?"
        )
    if "celibataire" not in decote or "couple" not in decote:
        raise ValueError(
            f"ir_2026.json : décote manquante pour {set(['celibataire', 'couple']) - set(decote)}. "
            f"Vérifie les libellés 'décote ... célibataire' et 'décote ... couple'."
        )
    if "plafond_demi_part" not in quotient_familial:
        raise ValueError(
            "ir_2026.json : plafond quotient familial manquant. "
            "Vérifie le libellé 'quotient familial ... plafond'."
        )

    return tranches, decote, quotient_familial


def _ir_par_part(rni_par_part: float, tranches: list) -> float:
    """Calcule l'IR brut pour un niveau de revenu par part."""
    ir = 0.0
    for t in tranches:
        if rni_par_part <= t["min"]:
            break
        t_max = t["max"] if t["max"] is not None else float("inf")
        base = min(rni_par_part, t_max) - t["min"]
        ir += base * t["rate"]
    return max(0.0, ir)


def calcul_ir(rni: float, parts: float, situation: str) -> dict:
    """
    Calcule l'IR net 2026 d'un foyer fiscal (revenus 2025).

    Étapes, dans l'ordre légal (CGI art. 197-I) :
      1. IR brut = somme(tranches progressives) × parts
      2. Plafonnement du quotient familial (CGI art. 197-I-2, plafond 1 807 €/demi-part)
      3. Décote pour faibles revenus (CGI art. 197-I-4, coefficient 0.4525)

    Hors scope de ce calculateur (à ajouter si pertinent) :
      - CEHR (contribution exceptionnelle hauts revenus) — CGI art. 223 sexies
      - Crédits et réductions d'impôt (emploi à domicile, dons, etc.)
      - Abattements spécifiques (journalistes, pensions, etc.)

    Args:
        rni: Revenu Net Imposable total du foyer (après abattements 10% salaires)
        parts: Nombre de parts fiscales (CGI art. 194)
        situation: "celibataire" ou "couple" (détermine le seuil de décote)

    Returns:
        Dict structuré avec toutes les étapes intermédiaires pour audit humain.
    """
    if rni < 0:
        raise ValueError(f"rni négatif interdit ({rni}). Un revenu négatif "
                         f"correspond à un déficit, traité en amont des abattements.")
    if parts <= 0:
        raise ValueError(f"parts doit être > 0 (reçu {parts}).")

    tranches, decote_params, qf_params = _load_bareme()

    parts_ref = 2.0 if situation == "couple" else 1.0
    rni_par_part = rni / parts if parts > 0 else 0.0

    # --- Étape 1 : IR brut avec les parts réelles ---
    ir_brut_par_part = _ir_par_part(rni_par_part, tranches)
    ir_brut_total = ir_brut_par_part * parts

    # --- Étape 2 : Plafonnement du quotient familial ---
    nb_demi_parts_supp = max(0.0, (parts - parts_ref) * 2)
    plafond_demi_part = qf_params.get("plafond_demi_part", 1807.0)
    plafond_gain_qf = plafond_demi_part * nb_demi_parts_supp

    ir_apres_qf = ir_brut_total
    qf_plafonne = False

    if nb_demi_parts_supp > 0:
        rni_par_part_ref = rni / parts_ref
        ir_ref = _ir_par_part(rni_par_part_ref, tranches) * parts_ref
        gain_qf = ir_ref - ir_brut_total
        if gain_qf > plafond_gain_qf:
            ir_apres_qf = ir_ref - plafond_gain_qf
            qf_plafonne = True

    # --- Étape 3 : Décote ---
    dp = decote_params.get(situation, decote_params["celibataire"])
    seuil_decote = dp["seuil_impot_brut"]
    plafond_decote = dp["plafond_decote"]

    decote = 0.0
    if 0 < ir_apres_qf < seuil_decote:
        decote = max(0.0, plafond_decote - COEFF_DECOTE * ir_apres_qf)

    ir_net = max(0.0, ir_apres_qf - decote)
    taux_moyen = (ir_net / rni * 100) if rni > 0 else 0.0

    # Détail par tranche pour l'affichage
    detail_tranches = []
    for t in tranches:
        if rni_par_part <= t["min"]:
            break
        t_max = t["max"] if t["max"] is not None else float("inf")
        base = min(rni_par_part, t_max) - t["min"]
        detail_tranches.append({
            "min": t["min"],
            "max": t["max"],
            "rate": t["rate"],
            "base_par_part": round(base, 2),
            "impot_par_part": round(base * t["rate"], 2),
        })

    return {
        "rni": round(rni, 2),
        "parts": parts,
        "situation": situation,
        "rni_par_part": round(rni_par_part, 2),
        "detail_tranches": detail_tranches,
        "ir_brut_total": round(ir_brut_total, 2),
        "nb_demi_parts_supp": nb_demi_parts_supp,
        "plafond_gain_qf": round(plafond_gain_qf, 2),
        "qf_plafonne": qf_plafonne,
        "ir_apres_qf": round(ir_apres_qf, 2),
        "decote_seuil": seuil_decote,
        "decote_appliquee": round(decote, 2),
        "ir_net": round(ir_net, 2),
        "taux_moyen": round(taux_moyen, 2),
        "annee": 2026,
        "source": "data/rates/ir_2026.json",
    }


def _afficher(result: dict, tranches_raw: list) -> None:
    """Affiche le résultat sous forme de tableau lisible."""
    sep = "─" * 58

    print()
    print(f"  {'IMPÔT SUR LE REVENU 2026':^54}")
    print(f"  {'(revenus 2025 — barème loi n°2026-103)':^54}")
    print()
    print(f"  {'Revenu net imposable':<36} {result['rni']:>14,.0f} €")
    print(f"  {'Parts fiscales':<36} {result['parts']:>14.1f}")
    print(f"  {'Situation':<36} {result['situation']:>14}")
    print(f"  {'RNI par part':<36} {result['rni_par_part']:>14,.0f} €")
    print()
    print(f"  Barème progressif :")
    for t in result["detail_tranches"]:
        t_max = f"{t['max']:,.0f} €" if t["max"] else "et +"
        pct = f"{t['rate']*100:.0f}%"
        impot = t["impot_par_part"] * result["parts"]
        print(f"    {t['min']:>10,.0f} → {t_max:<12}  × {pct:<4}  = {impot:>10,.0f} €")

    print()
    print(f"  {'IR brut':<36} {result['ir_brut_total']:>14,.0f} €")

    if result["qf_plafonne"]:
        print(f"  {'Plafonnement QF (gain plafonné)':<36} {result['ir_apres_qf']:>14,.0f} €")
    elif result["nb_demi_parts_supp"] > 0:
        print(f"  {'Quotient familial (non plafonné)':<36} {result['ir_apres_qf']:>14,.0f} €")

    if result["decote_appliquee"] > 0:
        print(f"  {'Décote':<36} −{result['decote_appliquee']:>13,.0f} €")

    print()
    print(f"  {sep}")
    print(f"  {'IMPÔT NET':<36} {result['ir_net']:>14,.0f} €")
    print(f"  {'Taux moyen d\'imposition':<36} {result['taux_moyen']:>13.1f} %")
    print(f"  {sep}")
    print()
    print("  ⚠️  Je suis une IA. Ces chiffres sont indicatifs.")
    print("  Vérifie sur simulateur-ir-ifi.impots.gouv.fr avant de te fier au calcul.")
    print("  Décision importante (déclaration, redressement) : expert-comptable ou avocat fiscaliste.")
    print()


def _load_foyer(chemin: str) -> tuple[float, float, str]:
    """
    Extrait RNI, parts et situation depuis foyer.json (clés françaises).
    Retourne (rni, parts, situation).
    """
    with open(chemin, encoding="utf-8") as f:
        foyer = json.load(f)

    revenus = foyer.get("revenus", {})
    rni = 0.0

    for sal in revenus.get("salaires", []):
        net = sal.get("net_imposable_annuel", 0)
        brut = sal.get("brut_annuel", 0)
        if net > 0:
            rni += net
        elif brut > 0:
            # Abattement 10% (plancher 495€, plafond 14 645€)
            abattement = min(max(brut * 0.10, 495.0), 14645.0)
            rni += brut - abattement

    for ind in revenus.get("independant", []):
        ca = ind.get("chiffre_affaires_annuel", 0)
        charges = ind.get("charges_annuelles", 0)
        rni += ca - charges

    rf = revenus.get("revenus_financiers", {})
    rni += rf.get("dividendes", 0)
    rni += rf.get("interets", 0)
    rni += rf.get("plus_values_mobilieres", 0)
    rni += rf.get("plus_values_immobilieres", 0)
    rni += revenus.get("pensions_allocations", 0)

    deductions = foyer.get("deductions", {})
    rni -= deductions.get("versements_per", 0)
    rni -= deductions.get("pension_alimentaire_versee", 0)

    parts = float(foyer.get("foyer_fiscal", {}).get("parts_fiscales", 1.0))

    declarants = foyer.get("foyer_fiscal", {}).get("declarants", [])
    situation = "celibataire"
    for d in declarants:
        if d.get("situation_familiale") in ("marie", "pacse"):
            situation = "couple"
            break
    if len(declarants) >= 2:
        situation = "couple"

    return max(0.0, rni), parts, situation


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcul IR 2026 (revenus 2025) — Marcel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python scripts/calcul_ir.py --rni 45000 --parts 1
  python scripts/calcul_ir.py --rni 80000 --parts 2.5 --situation couple
  python scripts/calcul_ir.py --foyer foyer.json
  python scripts/calcul_ir.py --rni 45000 --json
""",
    )

    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--foyer", metavar="FICHIER",
                     help="Chemin vers foyer.json (lecture automatique)")
    src.add_argument("--rni", type=float, metavar="MONTANT",
                     help="Revenu Net Imposable total du foyer (€)")

    parser.add_argument("--parts", type=float, default=1.0,
                        help="Parts fiscales (défaut: 1.0)")
    parser.add_argument("--situation", choices=["celibataire", "couple"],
                        default="celibataire",
                        help="Pour le calcul de la décote (défaut: celibataire)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Sortie JSON structurée")

    args = parser.parse_args()

    try:
        tranches, _, _ = _load_bareme()
    except FileNotFoundError:
        print(f"Erreur : {RATES_FILE} introuvable.", file=sys.stderr)
        sys.exit(1)

    if args.foyer:
        try:
            rni, parts, situation = _load_foyer(args.foyer)
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Erreur lecture {args.foyer} : {e}", file=sys.stderr)
            sys.exit(1)
    else:
        rni, parts, situation = args.rni, args.parts, args.situation

    result = calcul_ir(rni, parts, situation)

    if args.json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _afficher(result, tranches)


if __name__ == "__main__":
    main()
