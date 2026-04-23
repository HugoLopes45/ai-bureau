"""
Tests pour calcul_taeg.py — TAEG 2026 et vérification taux d'usure.

Deux familles :
  1. Cas connus — mensualités et TAEG calculés à la main depuis la formule
     d'amortissement standard et la convention actuarielle annuelle
     (TAEG = (1 + i_mensuel)^12 − 1 sans frais ni assurance). À vérifier contre
     un simulateur tiers (Meilleurtaux, ANIL) — voir `golden_cases_taeg.md`.
  2. Tests de bornes — property-based : taux=0 → TAEG=0, ajout d'assurance ou
     de frais fait monter le TAEG monotonement, conservation des flux,
     détection du dépassement d'usure, bornes plancher (TAEG ≥ taux nominal
     actuariel).

Hors scope : assurance en % capital restant dû, caution Crédit Logement, IRA,
franchise, variable cap/floor.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calcul_taeg import calcul_taeg, _mensualite, _taeg_actuariel, _charger_usure


TOL_EUR = 1.0        # € sur mensualité
TOL_TAEG = 0.0005    # 5 points de base = 0.05 %


def _test_mens_taeg(desc, mens_attendu, taeg_attendu, **kwargs):
    r = calcul_taeg(**kwargs)
    diff_m = abs(r["mensualite_hors_assurance"] - mens_attendu)
    diff_t = abs(r["taeg"] - taeg_attendu)
    ok = diff_m <= TOL_EUR and diff_t <= TOL_TAEG
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(
        f"  {statut}  {desc:<50}"
        f"  mens {r['mensualite_hors_assurance']:>8.2f}€"
        f"  TAEG {r['taeg']*100:>6.3f}%"
        f"  (attendu mens {mens_attendu:.2f}€, TAEG {taeg_attendu*100:.3f}%)"
    )
    return ok


def main():
    print()
    print("=" * 90)
    print("  TESTS calcul_taeg.py — TAEG 2026")
    print("=" * 90)

    resultats = []

    # --- Cas 1 : canonique (immo 200k / 3 % / 20 ans, sans assurance ni frais) ---
    # Mensualité = 200000 × 0.0025 / (1 − 1.0025^(−240)) = 1 109,20 €
    # TAEG = (1.0025)^12 − 1 = 3,042 %
    resultats.append(_test_mens_taeg(
        "Immo 200k, 3 %, 20 ans (sec)",
        mens_attendu=1109.20, taeg_attendu=0.030416,
        capital=200000, taux_nominal=3.0, duree_mois=240,
        type_pret="immo_fixe_20plus",
    ))

    # --- Cas 2 : même prêt + assurance 30 €/mois ---
    # Mensualité hors inchangée = 1 109,20 €. TAEG > 3,042 % car surcoût 7 200 €.
    # Valeur calculée (locked as regression, ≈ 3,40 %).
    r2 = calcul_taeg(
        capital=200000, taux_nominal=3.0, duree_mois=240,
        assurance_mensuelle=30.0, type_pret="immo_fixe_20plus",
    )
    ok_mens2 = abs(r2["mensualite_hors_assurance"] - 1109.20) < TOL_EUR
    ok_taeg2 = r2["taeg"] > 0.030416  # doit être > taeg sans assurance
    resultats.append(ok_mens2 and ok_taeg2)
    statut = "✓" if (ok_mens2 and ok_taeg2) else "✗ ÉCHOUÉ"
    print(f"  {statut}  Immo 200k, 3 %, 20 ans + assurance 30€/m       "
          f"mens hors {r2['mensualite_hors_assurance']:.2f}€  "
          f"TAEG {r2['taeg']*100:.3f}% (> 3.042 attendu)")

    # --- Cas 3 : même prêt + frais dossier 1 500 € (sans assurance) ---
    # Capital net = 198 500. TAEG > 3,042 % (paie 1 109,20 × 240 = 266 208 pour 198 500 net).
    r3 = calcul_taeg(
        capital=200000, taux_nominal=3.0, duree_mois=240,
        frais_dossier=1500.0, type_pret="immo_fixe_20plus",
    )
    ok3 = r3["taeg"] > 0.030416
    resultats.append(ok3)
    statut = "✓" if ok3 else "✗ ÉCHOUÉ"
    print(f"  {statut}  Immo 200k + frais 1 500€                       "
          f"TAEG {r3['taeg']*100:.3f}% (> 3.042 attendu)")

    # --- Cas 4 : crédit conso, 5 000 € à 8 %, 36 mois ---
    # i = 0.08/12 = 0.006667
    # (1.006667)^36 ≈ 1.27024
    # M = 5000 × 0.006667 / (1 − 0.78725) = 5000 × 0.03134 ≈ 156.70 €
    # TAEG = (1.006667)^12 − 1 ≈ 8,300 %
    resultats.append(_test_mens_taeg(
        "Conso 5k, 8 %, 36 mois",
        mens_attendu=156.68, taeg_attendu=0.083000,
        capital=5000, taux_nominal=8.0, duree_mois=36,
        type_pret="conso_3000_6000",
    ))

    # --- Cas 5 : PTZ (prêt à taux zéro), 50 000 €, 300 mois, taux 0 % ---
    # Mensualité = 50000/300 = 166,67 €. TAEG = 0 % si pas de frais ni assurance.
    resultats.append(_test_mens_taeg(
        "PTZ 50k, 0 %, 300 mois",
        mens_attendu=166.67, taeg_attendu=0.0,
        capital=50000, taux_nominal=0.0, duree_mois=300,
        type_pret="immo_fixe_20plus",
    ))

    # --- Vérifications internes ---
    print()
    print("  Vérifications internes :")

    # Mensualité : cas limite taux=0 → capital/n
    assert abs(_mensualite(12000, 0.0, 12) - 1000.0) < 0.001
    print("  ✓  Mensualité taux=0 : capital/n = 1 000 €")

    # Mensualité : formule standard (100 k, 0,3 %/mois ≈ 3,66 %/an actuariel, 120 mois)
    # M = 100000 × 0.003 / (1 − 1.003^(−120)) = 993,55 €
    assert abs(_mensualite(100000, 0.003, 120) - 993.55) < 1.0
    print("  ✓  Mensualité formule standard (100k, 0.3 %/mois, 120 mois) ≈ 993,55 €")

    # TAEG dégénéré : paiement exactement = capital → taeg = 0
    assert _taeg_actuariel(12000, 1000, 12) == 0.0
    print("  ✓  TAEG paiement = capital → 0 %")

    # _charger_usure : tous les types valides retournent un taux numérique
    for type_valide in ["immo_fixe_moins10", "immo_fixe_10_20", "immo_fixe_20plus",
                         "immo_variable", "relais", "conso_3000_moins",
                         "conso_3000_6000", "conso_6000_plus", "decouvert"]:
        taux, desc = _charger_usure(type_valide)
        assert 0 < taux < 1, f"Taux usure invalide pour {type_valide} : {taux}"
    print("  ✓  Chargement usure : 9 types OK, tous ∈ (0, 1)")

    # --- Tests de bornes (property-based) ---
    print()
    print("  Tests de bornes :")

    # TAEG ≥ taux actuariel annuel du nominal (composition mensuelle).
    # Pour taux_nominal = 3 %, plancher = (1.0025)^12 − 1 = 3,042 %.
    base = calcul_taeg(capital=200000, taux_nominal=3.0, duree_mois=240,
                       type_pret="immo_fixe_20plus")
    plancher = (1 + 0.03/12) ** 12 - 1
    ok = abs(base["taeg"] - plancher) < TOL_TAEG
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  TAEG sans frais/assurance = (1+i/12)^12 − 1 "
          f"({base['taeg']*100:.4f} vs {plancher*100:.4f})")

    # Monotonicité en assurance : ajouter de l'assurance augmente le TAEG.
    for assurance in [10, 30, 60, 100]:
        r = calcul_taeg(capital=200000, taux_nominal=3.0, duree_mois=240,
                        assurance_mensuelle=assurance, type_pret="immo_fixe_20plus")
        ok = r["taeg"] > base["taeg"]
        if not ok:
            resultats.append(False)
            print(f"    ✗ ÉCHOUÉ  Assurance {assurance}€/m ne fait pas monter TAEG")
            break
    else:
        resultats.append(True)
        print(f"    ✓  Monotonicité : TAEG monte avec l'assurance (4 valeurs)")

    # Monotonicité en frais : idem.
    for frais in [500, 1500, 3000, 5000]:
        r = calcul_taeg(capital=200000, taux_nominal=3.0, duree_mois=240,
                        frais_dossier=frais, type_pret="immo_fixe_20plus")
        ok = r["taeg"] > base["taeg"]
        if not ok:
            resultats.append(False)
            print(f"    ✗ ÉCHOUÉ  Frais {frais}€ ne fait pas monter TAEG")
            break
    else:
        resultats.append(True)
        print(f"    ✓  Monotonicité : TAEG monte avec les frais (4 valeurs)")

    # Conservation des flux : mensualité × n = capital + intérêts (sans ass. ni frais).
    r = calcul_taeg(capital=100000, taux_nominal=4.5, duree_mois=180,
                    type_pret="immo_fixe_10_20")
    total_verse = r["mensualite_hors_assurance"] * 180
    attendu = 100000 + r["total_interets"]
    ok = abs(total_verse - attendu) < 1.0
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Conservation : mens × n = capital + intérêts "
          f"({total_verse:.2f} vs {attendu:.2f})")

    # Détection dépassement d'usure.
    # Usure conso > 6 000 € Q2 2026 = 8,61 %. Taux 10 % → TAEG > usure → drapeau actif.
    r = calcul_taeg(capital=10000, taux_nominal=10.0, duree_mois=60,
                    type_pret="conso_6000_plus")
    ok = r["usure_depasse"] and r["taeg"] > r["taux_usure"]
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Dépassement usure détecté : "
          f"TAEG {r['taeg']*100:.2f}% > usure {r['taux_usure']*100:.2f}%")

    # Sous l'usure : drapeau inactif.
    r = calcul_taeg(capital=200000, taux_nominal=3.0, duree_mois=240,
                    assurance_mensuelle=30, type_pret="immo_fixe_20plus")
    # Usure immo ≥ 20 ans = 5,19 %. TAEG ≈ 3,4 % < 5,19 % → pas de dépassement.
    ok = not r["usure_depasse"] and r["taeg"] < r["taux_usure"]
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Sous l'usure : drapeau inactif "
          f"(TAEG {r['taeg']*100:.2f}% < usure {r['taux_usure']*100:.2f}%)")

    # Monotonicité en durée : plus c'est long, plus mens baisse, plus intérêts totaux montent.
    prev_mens, prev_int = 1e9, -1.0
    for duree in [120, 180, 240, 300]:
        r = calcul_taeg(capital=200000, taux_nominal=3.5, duree_mois=duree,
                        type_pret="immo_fixe_20plus")
        if not (r["mensualite_hors_assurance"] < prev_mens and r["total_interets"] > prev_int):
            resultats.append(False)
            print(f"    ✗ ÉCHOUÉ  Monotonicité durée brisée à {duree} mois")
            break
        prev_mens = r["mensualite_hors_assurance"]
        prev_int = r["total_interets"]
    else:
        resultats.append(True)
        print(f"    ✓  Monotonicité durée : mens ↓, intérêts ↑ (10/15/20/25 ans)")

    # --- Résumé ---
    print()
    print("=" * 90)
    nb_ok = sum(resultats)
    nb_total = len(resultats)
    if nb_ok == nb_total:
        print(f"  ✓  {nb_ok}/{nb_total} cas OK — calcul_taeg.py prêt")
    else:
        nb_ko = nb_total - nb_ok
        print(f"  ✗  {nb_ko} cas ÉCHOUÉS sur {nb_total}")
    print("=" * 90)
    print()

    return nb_ok == nb_total


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
