#!/usr/bin/env python3
"""
calcul_taeg.py — TAEG 2026 + vérification taux d'usure — Marcel

Usage:
    python scripts/calcul_taeg.py --capital 200000 --taux 3.0 --duree 240
    python scripts/calcul_taeg.py --capital 200000 --taux 3.0 --duree 240 --assurance 30 --frais 1500
    python scripts/calcul_taeg.py --capital 5000 --taux 8.0 --duree 36 --type conso_3000_6000
    python scripts/calcul_taeg.py --capital 300000 --taux 3.5 --duree 300 --assurance 45 --json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _freshness import check_freshness

ROOT = Path(__file__).parent.parent
RATES_FILE = ROOT / "data" / "rates" / "taux_usure_2026_q2.json"

# Mapping type_pret → fragment de libellé recherché dans le JSON usure.
# Garde le mapping côté code (structurel), les valeurs côté JSON (taux variables).
TYPES_USURE = {
    "immo_fixe_moins10":    ("taux fixe < 10 ans",   "< 10 ans"),
    "immo_fixe_10_20":      ("taux fixe 10–20 ans",  "10 à 20 ans"),
    "immo_fixe_20plus":     ("taux fixe ≥ 20 ans",   "≥ 20 ans"),
    "immo_variable":        ("taux variable",         "taux variable"),
    "relais":               ("crédit relais",         "relais (prêt court terme)"),
    "conso_3000_moins":     ("consommation ≤ 3",      "conso ≤ 3 000 €"),
    "conso_3000_6000":      ("consommation 3",        "conso 3 000–6 000 €"),
    "conso_6000_plus":      ("consommation > 6 000",  "conso > 6 000 €"),
    "decouvert":            ("découvert",             "découvert bancaire"),
}


def _charger_usure(type_pret: str) -> tuple[float, str]:
    """
    Retourne (taux_usure_en_fraction, description) pour le type demandé.

    Sources (via JSON) :
      - Taux d'usure : Banque de France, publication trimestrielle
        (Code monétaire et financier art. L. 313-1)
    """
    if type_pret not in TYPES_USURE:
        raise ValueError(
            f"type_pret '{type_pret}' invalide. "
            f"Valeurs acceptées : {list(TYPES_USURE.keys())}"
        )

    with open(RATES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    check_freshness(data, "taux_usure_2026_q2.json")

    fragment, description = TYPES_USURE[type_pret]
    frag_lower = fragment.lower()

    for item in data["donnees"]:
        label = item["item"].lower()
        val = item["value"]
        if not isinstance(val, (int, float)):
            continue  # skip l'entrée "prochaine mise à jour" (value=null)
        if frag_lower in label:
            return float(val) / 100, description

    raise ValueError(
        f"taux_usure_2026_q2.json : aucun taux trouvé pour type '{type_pret}' "
        f"(fragment recherché : '{fragment}')."
    )


def _mensualite(capital: float, taux_mensuel: float, n: int) -> float:
    """
    Mensualité d'un prêt à remboursement constant (formule amortissement standard).

    Cas dégénéré taux=0 : M = capital / n.
    Sinon : M = C × i / (1 − (1+i)^(−n)).
    """
    if taux_mensuel == 0:
        return capital / n
    return capital * taux_mensuel / (1 - (1 + taux_mensuel) ** (-n))


def _taeg_actuariel(capital_net: float, mensualite_totale: float, n: int) -> float:
    """
    Résout i_m tel que capital_net = mensualite_totale × (1 − (1+i_m)^(−n)) / i_m.
    Retourne TAEG annuel = (1 + i_m)^12 − 1.

    Méthode : bissection. Plus lent que Newton-Raphson mais toujours convergent
    et sans calcul de dérivée. 100 itérations → précision ~1e-16.

    Cas dégénéré : si la somme des mensualités = capital net (à 1 centime près),
    le taux effectif est 0.
    """
    if capital_net <= 0 or mensualite_totale <= 0:
        raise ValueError(
            f"TAEG : capital_net={capital_net}, mens={mensualite_totale} invalides"
        )

    total_paye = mensualite_totale * n
    if abs(total_paye - capital_net) < 0.01:
        return 0.0
    if total_paye < capital_net:
        # L'emprunteur paie moins que le capital reçu — impossible dans un prêt réel.
        raise ValueError(
            f"TAEG : total payé ({total_paye:.2f}) < capital net ({capital_net:.2f}). "
            f"Mensualités insuffisantes pour rembourser le capital."
        )

    def f(i: float) -> float:
        """Écart : valeur actuelle des mensualités moins capital net. > 0 si taux trop bas."""
        if i == 0:
            return total_paye - capital_net
        return mensualite_totale * (1 - (1 + i) ** (-n)) / i - capital_net

    # Bissection. Borne haute 1.0 = 100 %/mois, largement au-dessus de tout prêt réel.
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid  # taux trop bas
        else:
            hi = mid  # taux trop haut
        if hi - lo < 1e-12:
            break

    i_m = (lo + hi) / 2
    return (1 + i_m) ** 12 - 1


def calcul_taeg(
    capital: float,
    taux_nominal: float,
    duree_mois: int,
    assurance_mensuelle: float = 0.0,
    frais_dossier: float = 0.0,
    type_pret: str = "immo_fixe_20plus",
) -> dict:
    """
    Calcule mensualité, TAEG actuariel, coût total et vérifie vs taux d'usure.

    Étapes (Code de la consommation art. L. 314-1, méthode R. 314-1) :
      1. Mensualité hors assurance = amortissement constant.
      2. Mensualité totale = mensualité + prime d'assurance mensuelle.
      3. Coût total crédit = total payé − capital + frais dossier.
      4. TAEG = taux actuariel annuel qui équalise capital net (capital − frais)
         et somme actualisée des mensualités totales.
      5. Vérification : TAEG ≤ taux d'usure applicable (Banque de France trimestriel).

    Hors scope :
      - Assurance en % du capital restant dû (amortissement) — ici prime constante.
      - Caution Crédit Logement vs hypothèque — non modélisée (≈ 0.5–1 % du capital,
        à ajouter aux frais_dossier en première approximation).
      - Pénalités remboursement anticipé (IRA) — hors calcul TAEG par convention.
      - Période différée (franchise partielle/totale) — pas couverte.
      - Taux variables avec cap/floor — `immo_variable` utilise le taux initial seul.

    Args:
        capital: Montant emprunté (€).
        taux_nominal: Taux débiteur annuel hors assurance (%, ex: 3.5).
        duree_mois: Durée du prêt en mois.
        assurance_mensuelle: Prime d'assurance mensuelle constante (€/mois).
        frais_dossier: Frais imputés au démarrage (€, déduits du capital net).
        type_pret: cf. TYPES_USURE.

    Returns:
        Dict avec mensualité, TAEG, coût, vérif usure, détail pour audit.
    """
    # --- Guards d'entrée ---
    if capital <= 0:
        raise ValueError(f"capital doit être > 0 (reçu {capital})")
    if duree_mois <= 0:
        raise ValueError(f"duree_mois doit être > 0 (reçu {duree_mois})")
    if taux_nominal < 0:
        raise ValueError(f"taux_nominal négatif interdit ({taux_nominal})")
    if assurance_mensuelle < 0:
        raise ValueError(f"assurance_mensuelle négative interdite ({assurance_mensuelle})")
    if frais_dossier < 0:
        raise ValueError(f"frais_dossier négatifs interdits ({frais_dossier})")
    if frais_dossier >= capital:
        raise ValueError(
            f"frais_dossier ({frais_dossier}) ≥ capital ({capital}). "
            f"Le capital net reçu serait ≤ 0 — impossible."
        )

    # --- Chargement usure ---
    taux_usure, usure_description = _charger_usure(type_pret)

    # --- Mensualité ---
    i_mensuel = taux_nominal / 100 / 12
    mens_ha = _mensualite(capital, i_mensuel, duree_mois)
    mens_totale = mens_ha + assurance_mensuelle

    # --- Coûts ---
    total_interets = mens_ha * duree_mois - capital
    total_assurance = assurance_mensuelle * duree_mois
    cout_total = total_interets + total_assurance + frais_dossier

    # --- TAEG actuariel ---
    capital_net = capital - frais_dossier
    taeg = _taeg_actuariel(capital_net, mens_totale, duree_mois)

    # --- Check usure ---
    usure_depasse = taeg > taux_usure

    return {
        "capital": round(capital, 2),
        "taux_nominal": round(taux_nominal, 4),
        "duree_mois": duree_mois,
        "assurance_mensuelle": round(assurance_mensuelle, 2),
        "frais_dossier": round(frais_dossier, 2),
        "type_pret": type_pret,
        "type_pret_description": usure_description,

        "mensualite_hors_assurance": round(mens_ha, 2),
        "mensualite_totale": round(mens_totale, 2),

        "total_interets": round(total_interets, 2),
        "total_assurance": round(total_assurance, 2),
        "frais_dossier_total": round(frais_dossier, 2),
        "cout_total_credit": round(cout_total, 2),

        "taeg": round(taeg, 6),
        "taeg_pct": round(taeg * 100, 3),
        "taux_usure": round(taux_usure, 6),
        "taux_usure_pct": round(taux_usure * 100, 3),
        "usure_depasse": usure_depasse,

        "annee": 2026,
        "source": "data/rates/taux_usure_2026_q2.json",
    }


def _afficher(r: dict) -> None:
    """Affiche le résultat sous forme de tableau lisible."""
    sep = "─" * 58

    print()
    print(f"  {'CRÉDIT — CALCUL TAEG 2026':^54}")
    print()
    print(f"  {'Capital emprunté':<36} {r['capital']:>14,.2f} €")
    print(f"  {'Taux nominal annuel':<36} {r['taux_nominal']:>14.3f} %")
    print(f"  {'Durée':<36} {r['duree_mois']:>11} mois "
          f"({r['duree_mois']/12:.1f} ans)")
    if r["assurance_mensuelle"] > 0:
        print(f"  {'Assurance mensuelle':<36} {r['assurance_mensuelle']:>14,.2f} €")
    if r["frais_dossier"] > 0:
        print(f"  {'Frais dossier':<36} {r['frais_dossier']:>14,.2f} €")
    print(f"  {'Type de prêt':<36} {r['type_pret_description']:>14}")
    print()

    print(f"  {sep}")
    print(f"  {'MENSUALITÉ HORS ASSURANCE':<36} {r['mensualite_hors_assurance']:>11,.2f} €/m")
    if r["assurance_mensuelle"] > 0:
        print(f"  {'MENSUALITÉ TOTALE (avec assurance)':<36} {r['mensualite_totale']:>11,.2f} €/m")
    print(f"  {sep}")

    print()
    print(f"  Coût du crédit :")
    print(f"    Intérêts          = {r['total_interets']:>12,.2f} €")
    if r["total_assurance"] > 0:
        print(f"    Assurance totale  = {r['total_assurance']:>12,.2f} €")
    if r["frais_dossier_total"] > 0:
        print(f"    Frais dossier     = {r['frais_dossier_total']:>12,.2f} €")
    print(f"    COÛT TOTAL        = {r['cout_total_credit']:>12,.2f} €")

    label_taeg = "TAEG (annuel actuariel)"
    label_usure = "Taux d'usure applicable"
    label_marge = "Marge sous l'usure"
    print()
    print(f"  {sep}")
    print(f"  {label_taeg:<36} {r['taeg_pct']:>13.3f} %")
    print(f"  {label_usure:<36} {r['taux_usure_pct']:>13.3f} %")
    if r["usure_depasse"]:
        print(f"  {sep}")
        print(f"  ⛔  TAEG > taux d'usure → CONTRAT ILLÉGAL")
        print(f"      Une banque ne peut PAS te proposer ce prêt. Renégocie.")
    else:
        marge = r["taux_usure_pct"] - r["taeg_pct"]
        print(f"  {label_marge:<36} {marge:>13.3f} points")
    print(f"  {sep}")

    print()
    print("  ⚠️  Je suis une IA. Ces chiffres sont indicatifs.")
    print("  Vérifie le taux d'usure sur banque-france.fr et l'offre exacte de la banque.")
    print("  Négociation ou dossier complexe : consulte un courtier IOBSP agréé ORIAS.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcul TAEG 2026 + vérification taux d'usure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python scripts/calcul_taeg.py --capital 200000 --taux 3.0 --duree 240
  python scripts/calcul_taeg.py --capital 200000 --taux 3.0 --duree 240 --assurance 30 --frais 1500
  python scripts/calcul_taeg.py --capital 5000 --taux 8.0 --duree 36 --type conso_3000_6000
""",
    )
    parser.add_argument("--capital", type=float, required=True, metavar="MONTANT",
                        help="Capital emprunté (€)")
    parser.add_argument("--taux", type=float, required=True, dest="taux_nominal",
                        metavar="PCT",
                        help="Taux nominal annuel hors assurance (%% — ex: 3.5)")
    parser.add_argument("--duree", type=int, required=True, dest="duree_mois",
                        metavar="MOIS",
                        help="Durée du prêt en mois (240 = 20 ans)")
    parser.add_argument("--assurance", type=float, default=0.0,
                        dest="assurance_mensuelle", metavar="EUR",
                        help="Prime d'assurance mensuelle fixe (€, défaut 0)")
    parser.add_argument("--frais", type=float, default=0.0,
                        dest="frais_dossier", metavar="EUR",
                        help="Frais de dossier au démarrage (€, défaut 0)")
    parser.add_argument("--type", default="immo_fixe_20plus",
                        dest="type_pret", choices=list(TYPES_USURE.keys()),
                        help="Type de prêt (défaut: immo_fixe_20plus)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Sortie JSON structurée")
    args = parser.parse_args()

    try:
        result = calcul_taeg(
            capital=args.capital,
            taux_nominal=args.taux_nominal,
            duree_mois=args.duree_mois,
            assurance_mensuelle=args.assurance_mensuelle,
            frais_dossier=args.frais_dossier,
            type_pret=args.type_pret,
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
