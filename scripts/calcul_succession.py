#!/usr/bin/env python3
"""
calcul_succession.py — Droits de succession 2026 (un héritier à la fois) — Marcel

Usage:
    python scripts/calcul_succession.py --actif 300000 --lien enfant
    python scripts/calcul_succession.py --actif 50000 --lien frere_soeur --handicape
    python scripts/calcul_succession.py --actif 200000 --lien enfant --donations-15-ans 60000
    python scripts/calcul_succession.py --actif 1000000 --lien conjoint --json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _freshness import check_freshness

ROOT = Path(__file__).parent.parent
RATES_FILE = ROOT / "data" / "rates" / "succession_dons_2026.json"

# Liens de parenté acceptés.
LIENS_VALIDES = (
    "conjoint",             # exonération totale (loi TEPA 2007)
    "enfant",               # abattement 100 000 €, barème ligne directe
    "parent",               # idem enfant (réciprocité en ligne directe)
    "petit_enfant",         # abattement 31 865 €, barème ligne directe
    "arriere_petit_enfant", # abattement 5 310 €, barème ligne directe
    "frere_soeur",          # abattement 15 932 €, barème 35 %/45 %
    "neveu_niece",          # abattement 7 967 €, taux forfait 55 %
    "quatrieme_degre",      # oncle, tante, cousin germain : abattement 1 594 €, taux 55 %
    "non_parent",           # concubin non PACS, ami : abattement 1 594 €, taux 60 %
)


def _charger_parametres() -> dict:
    """
    Charge abattements et barèmes depuis succession_dons_2026.json.

    Sources (via JSON) :
      - Abattements : CGI art. 779 (enfant 100 k, frère/sœur, handicapé +159 325)
      - Exonération conjoint/PACS : CGI art. 796-0 bis (loi TEPA 21/08/2007)
      - Barème ligne directe : CGI art. 777, 7 tranches (5, 10, 15, 20, 30, 40, 45 %)
      - Barème frère/sœur : CGI art. 777, 2 tranches (35 %, 45 %)
      - Taux forfaitaires : CGI art. 777 (4e degré 55 %, non-parents 60 %)
      - Rappel fiscal : CGI art. 784 (donations reçues dans les 15 ans)
    """
    with open(RATES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    check_freshness(data, "succession_dons_2026.json")

    abat = {
        "enfant": None, "petit_enfant": None, "arriere_petit_enfant": None,
        "frere_soeur": None, "neveu_niece": None,
        "autres": None, "handicape_bonus": None,
    }
    bareme_ld = []  # ligne directe
    bareme_fs = []  # frère/sœur
    taux_4e = None
    taux_np = None  # non-parent

    for item in data["donnees"]:
        label = item["item"].lower()
        val = item["value"]

        # --- Abattements (valeurs scalaires en €) ---
        if "abattement en ligne directe descendante" in label:
            abat["enfant"] = float(val)
        elif "abattement petit-enfant" in label:
            abat["petit_enfant"] = float(val)
        elif "abattement arrière-petit-enfant" in label:
            abat["arriere_petit_enfant"] = float(val)
        elif "abattement frère ou sœur" in label:
            abat["frere_soeur"] = float(val)
        elif "abattement neveu ou nièce" in label:
            abat["neveu_niece"] = float(val)
        elif "abattement personnes handicapées" in label:
            abat["handicape_bonus"] = float(val)
        elif "abattement autres" in label:
            abat["autres"] = float(val)

        # --- Barèmes (dicts {min, max, rate}) ---
        elif "en ligne directe" in label and "barème" in label and isinstance(val, dict):
            bareme_ld.append({"min": val["min"], "max": val["max"], "rate": val["rate"]})
        elif "entre frères et sœurs" in label and "barème" in label and isinstance(val, dict):
            bareme_fs.append({"min": val["min"], "max": val["max"], "rate": val["rate"]})

        # --- Taux forfaitaires (percent scalaire) ---
        # IMPORTANT : tester "non-parents" avant "4ème degré", car l'étiquette
        # non-parent contient "au-delà du 4ème degré" et matcherait les deux.
        elif "non-parents" in label:
            taux_np = float(val)
        elif "4ème degré" in label or "4e degré" in label:
            taux_4e = float(val)

    bareme_ld.sort(key=lambda t: t["min"])
    bareme_fs.sort(key=lambda t: t["min"])

    # "parent" = réciproque de "enfant" — même abattement (CGI art. 779 I)
    abat["parent"] = abat["enfant"]

    # Garde-fou : détecter un drift de libellé JSON qui laisserait une valeur
    # silencieusement manquante. Meilleur d'échouer fort au boot que TypeError
    # au milieu du calcul (cf. bug "non-parents"/"4ème degré" déjà attrapé).
    abat_manquants = [k for k, v in abat.items() if v is None]
    if abat_manquants:
        raise ValueError(
            f"succession_dons_2026.json : abattements manquants : {abat_manquants}. "
            f"Libellés JSON renommés ?"
        )
    if len(bareme_ld) != 7:
        raise ValueError(
            f"succession_dons_2026.json : {len(bareme_ld)} tranches ligne directe "
            f"chargées (7 attendues)."
        )
    if len(bareme_fs) != 2:
        raise ValueError(
            f"succession_dons_2026.json : {len(bareme_fs)} tranches frère/sœur "
            f"chargées (2 attendues)."
        )
    if taux_4e is None or taux_np is None:
        raise ValueError(
            f"succession_dons_2026.json : taux forfaitaires manquants "
            f"(4e degré={taux_4e}, non-parent={taux_np})."
        )

    return {
        "abattements": abat,
        "bareme_ligne_directe": bareme_ld,
        "bareme_frere_soeur": bareme_fs,
        "taux_4e_degre": taux_4e,
        "taux_non_parent": taux_np,
    }


def _progressif(base: float, bareme: list) -> tuple[float, list]:
    """
    Applique un barème progressif. Retourne (droits, détail_par_tranche)
    pour affichage audit.
    """
    droits = 0.0
    detail = []
    for t in bareme:
        if base <= t["min"]:
            break
        t_max = t["max"] if t["max"] is not None else float("inf")
        tranche = min(base, t_max) - t["min"]
        montant = tranche * t["rate"]
        droits += montant
        detail.append({
            "min": t["min"], "max": t["max"], "rate": t["rate"],
            "base": round(tranche, 2), "montant": round(montant, 2),
        })
    return max(0.0, droits), detail


def calcul_succession(
    actif_recu: float,
    lien_parente: str,
    handicape: bool = False,
    donations_15_ans: float = 0.0,
) -> dict:
    """
    Calcule les droits de succession dus par UN héritier.

    Étapes, dans l'ordre légal :
      1. Exonération conjoint / PACS (CGI art. 796-0 bis) → retour anticipé.
      2. Abattement de base selon lien de parenté (CGI art. 779).
      3. Abattement cumulé +159 325 € si bénéficiaire handicapé (art. 779 II).
      4. Abattement résiduel après rappel fiscal 15 ans (art. 784).
      5. Base taxable = max(0, actif reçu − abattement résiduel).
      6. Barème progressif (ligne directe ou frère/sœur) ou forfait (55 % ou 60 %).

    Hors scope :
      - Démembrement (CGI art. 669) — usufruit/nue-propriété non calculés.
      - Assurance-vie (CGI art. 990 I versements avant 70 ans, art. 757 B après).
      - Pacte Dutreil (CGI art. 787 B) — abattement 75 % transmission entreprise.
      - Dons spéciaux : don familial argent (art. 790 G, 31 865 €),
        don logement temporaire (2025-2026, jusqu'à 100 k€/donateur).
      - Partage civil entre cohéritiers (réserves héréditaires, quotité disponible).
      - Réduction art. 780 charges de famille (marginale, 305 € par enfant au-delà
        du 2e en ligne directe).

    Args:
        actif_recu: Part nette reçue par l'héritier (€, après déduction passif).
        lien_parente: cf. LIENS_VALIDES.
        handicape: True si l'héritier est reconnu handicapé (art. 779 II).
        donations_15_ans: Abattement déjà consommé via donations dans les 15 ans.

    Returns:
        Dict structuré avec toutes les étapes intermédiaires pour audit.
    """
    if lien_parente not in LIENS_VALIDES:
        raise ValueError(
            f"lien_parente '{lien_parente}' invalide. "
            f"Valeurs acceptées : {list(LIENS_VALIDES)}"
        )
    if actif_recu < 0:
        raise ValueError(f"actif_recu négatif interdit ({actif_recu}). "
                         f"Un passif supérieur à l'actif = renonciation, pas 'droits négatifs'.")
    if donations_15_ans < 0:
        raise ValueError(f"donations_15_ans négatif interdit ({donations_15_ans}). "
                         f"Une donation négative agrandirait l'abattement — bug silencieux.")

    params = _charger_parametres()
    abat = params["abattements"]

    # --- Étape 1 : Exonération conjoint/PACS ---
    if lien_parente == "conjoint":
        return {
            "actif_recu": round(actif_recu, 2),
            "lien_parente": "conjoint",
            "handicape": handicape,
            "exonere": True,
            "motif_exoneration": "loi TEPA 2007 — conjoint / PACS survivant",
            "abattement_base": None,
            "donations_15_ans": round(donations_15_ans, 2),
            "abattement_residuel": None,
            "base_taxable": 0.0,
            "bareme_type": "exonere",
            "detail_tranches": [],
            "droits": 0.0,
            "taux_moyen": 0.0,
            "annee": 2026,
            "source": "data/rates/succession_dons_2026.json",
        }

    # --- Étape 2 : Abattement de base selon lien ---
    # (lien, abattement_base, bareme_type)
    mapping = {
        "enfant":               (abat["enfant"],               "ligne_directe"),
        "parent":               (abat["parent"],               "ligne_directe"),
        "petit_enfant":         (abat["petit_enfant"],         "ligne_directe"),
        "arriere_petit_enfant": (abat["arriere_petit_enfant"], "ligne_directe"),
        "frere_soeur":          (abat["frere_soeur"],          "frere_soeur"),
        "neveu_niece":          (abat["neveu_niece"],          "forfait_55"),
        "quatrieme_degre":      (abat["autres"],               "forfait_55"),
        "non_parent":           (abat["autres"],               "forfait_60"),
    }
    abattement_base, bareme_type = mapping[lien_parente]

    # --- Étape 3 : Handicapé cumule +159 325 ---
    if handicape:
        abattement_base += abat["handicape_bonus"]

    # --- Étape 4 : Abattement résiduel (rappel 15 ans) ---
    abattement_residuel = max(0.0, abattement_base - donations_15_ans)

    # --- Étape 5 : Base taxable ---
    base_taxable = max(0.0, actif_recu - abattement_residuel)

    # --- Étape 6 : Barème ---
    if bareme_type == "ligne_directe":
        droits, detail = _progressif(base_taxable, params["bareme_ligne_directe"])
    elif bareme_type == "frere_soeur":
        droits, detail = _progressif(base_taxable, params["bareme_frere_soeur"])
    elif bareme_type == "forfait_55":
        droits = base_taxable * params["taux_4e_degre"]
        detail = [{"min": 0, "max": None, "rate": params["taux_4e_degre"],
                   "base": round(base_taxable, 2), "montant": round(droits, 2)}]
    elif bareme_type == "forfait_60":
        droits = base_taxable * params["taux_non_parent"]
        detail = [{"min": 0, "max": None, "rate": params["taux_non_parent"],
                   "base": round(base_taxable, 2), "montant": round(droits, 2)}]

    taux_moyen = (droits / actif_recu * 100) if actif_recu > 0 else 0.0

    return {
        "actif_recu": round(actif_recu, 2),
        "lien_parente": lien_parente,
        "handicape": handicape,
        "exonere": False,
        "abattement_base": round(abattement_base, 2),
        "donations_15_ans": round(donations_15_ans, 2),
        "abattement_residuel": round(abattement_residuel, 2),
        "base_taxable": round(base_taxable, 2),
        "bareme_type": bareme_type,
        "detail_tranches": detail,
        "droits": round(droits, 2),
        "taux_moyen": round(taux_moyen, 2),
        "annee": 2026,
        "source": "data/rates/succession_dons_2026.json",
    }


def _afficher(result: dict) -> None:
    """Affiche le résultat sous forme de tableau lisible."""
    sep = "─" * 58

    print()
    print(f"  {'DROITS DE SUCCESSION 2026':^54}")
    print()
    print(f"  {'Actif reçu':<36} {result['actif_recu']:>14,.2f} €")
    print(f"  {'Lien de parenté':<36} {result['lien_parente']:>14}")

    if result["exonere"]:
        print()
        print(f"  {sep}")
        print(f"  {'EXONÉRÉ DE DROITS':<36} {'0 €':>14}")
        print(f"  {sep}")
        print(f"\n  ({result['motif_exoneration']})\n")
        _disclaimer()
        return

    if result["handicape"]:
        print(f"  {'Handicapé (bonus +159 325 €)':<36} {'oui':>14}")

    print()
    print(f"  {'Abattement de base':<36} {result['abattement_base']:>14,.2f} €")
    if result["donations_15_ans"] > 0:
        print(f"  {'Donations dans les 15 ans':<36} −{result['donations_15_ans']:>13,.2f} €")
        print(f"  {'Abattement résiduel':<36} {result['abattement_residuel']:>14,.2f} €")
    print(f"  {'Base taxable':<36} {result['base_taxable']:>14,.2f} €")

    if result["base_taxable"] > 0:
        print()
        if result["bareme_type"].startswith("forfait"):
            taux = result["detail_tranches"][0]["rate"] * 100
            print(f"  Taux forfaitaire : {taux:.0f} %")
        else:
            print(f"  Barème progressif :")
            for t in result["detail_tranches"]:
                t_max = f"{t['max']:,.0f} €" if t["max"] else "et +"
                pct = f"{t['rate']*100:.0f}%"
                print(f"    {t['min']:>10,.0f} → {t_max:<12}  × {pct:<4}  = {t['montant']:>10,.2f} €")

    print()
    print(f"  {sep}")
    print(f"  {'DROITS DE SUCCESSION DUS':<36} {result['droits']:>14,.2f} €")
    if result["actif_recu"] > 0:
        print(f"  {'Taux moyen sur actif reçu':<36} {result['taux_moyen']:>13.1f} %")
    print(f"  {sep}")
    _disclaimer()


def _disclaimer() -> None:
    print()
    print("  ⚠️  Je suis une IA. Ces chiffres sont indicatifs.")
    print("  Vérifie sur impots.gouv.fr (je reçois une succession).")
    print("  Toute succession, donation ou testament : consulte obligatoirement un notaire.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcul des droits de succession 2026 (un héritier)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python scripts/calcul_succession.py --actif 300000 --lien enfant
  python scripts/calcul_succession.py --actif 50000 --lien frere_soeur --handicape
  python scripts/calcul_succession.py --actif 200000 --lien enfant --donations-15-ans 60000
""",
    )
    parser.add_argument("--actif", type=float, required=True, metavar="MONTANT",
                        help="Part nette reçue par l'héritier (€)")
    parser.add_argument("--lien", required=True, choices=list(LIENS_VALIDES),
                        help="Lien de parenté avec le défunt")
    parser.add_argument("--handicape", action="store_true",
                        help="Héritier reconnu handicapé (cumule +159 325 €)")
    parser.add_argument("--donations-15-ans", type=float, default=0.0,
                        dest="donations_15_ans", metavar="MONTANT",
                        help="Abattement déjà consommé via donations dans les 15 ans (€)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Sortie JSON structurée")
    args = parser.parse_args()

    try:
        result = calcul_succession(
            actif_recu=args.actif,
            lien_parente=args.lien,
            handicape=args.handicape,
            donations_15_ans=args.donations_15_ans,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)

    if args.json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _afficher(result)


if __name__ == "__main__":
    main()
