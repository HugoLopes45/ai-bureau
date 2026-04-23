"""
Tests pour calcul_are.py — ARE 2026.

Deux familles :
  1. Cas connus — valeurs à vérifier manuellement sur le simulateur France Travail.
     Voir `scripts/golden_cases_are.md` pour la procédure. Tant que ce doc n'est
     pas rempli, ces cas valident la cohérence interne du calculateur, pas sa
     conformité au simulateur officiel.
  2. Tests de bornes — property-based : continuité au croisement formule A/B,
     plancher actif sous seuil / inactif au-dessus, plafond jamais binding pour
     SJR réalistes, âges seuils, monotonicité cumul activité réduite, ARCE exact.

Hors scope : dégressivité hauts revenus (CGT art. R. 5422-2-1), intermittents,
prélèvements CSG/CRDS sur l'ARE.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calcul_are import calcul_are, _charger_parametres, _duree_max

TOLERANCE_JOUR = 1.0
TOLERANCE_MOIS = 30.0


def _test(desc, sjr, age, jours, attendu_jour, attendu_mois, **kwargs):
    result = calcul_are(sjr=sjr, age=age, jours_travailles=jours, **kwargs)
    diff_j = abs(result["are_nette_journaliere"] - attendu_jour)
    diff_m = abs(result["are_nette_mensuelle"] - attendu_mois)
    ok = diff_j <= TOLERANCE_JOUR and diff_m <= TOLERANCE_MOIS
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(
        f"  {statut}  {desc:<52}"
        f"  {attendu_jour:>7.2f} €/j → {result['are_nette_journaliere']:>7.2f} €/j"
        f"  {attendu_mois:>8.0f} €/m → {result['are_nette_mensuelle']:>8.0f} €/m"
    )
    return ok


def main():
    print()
    print("=" * 80)
    print("  TESTS calcul_are.py — ARE 2026")
    print("=" * 80)

    resultats = []

    # --- Cas bas de barème — plancher ---

    # SJR très bas (< 56.36) → formule B < plancher
    resultats.append(_test(
        "SJR 30€/j (plancher 32,13€)",
        sjr=30, age=40, jours=365,
        attendu_jour=32.13, attendu_mois=978.0,
    ))

    # --- Cas courants nouveau régime (depuis avril 2025) ---

    # SJR 50 — formule A domine (petit SJR, partie fixe pèse plus)
    resultats.append(_test(
        "SJR 50€/j, formule A domine (petit SJR)",
        sjr=50, age=42, jours=365,
        attendu_jour=33.38, attendu_mois=1015.0,
    ))

    # SJR 80 — cas représentatif, formule B légèrement supérieure
    resultats.append(_test(
        "SJR 80€/j, formule B ≈ formule A",
        sjr=80, age=42, jours=365,
        attendu_jour=45.60, attendu_mois=1387.0,
    ))

    # SJR 120 — formule B domine clairement
    resultats.append(_test(
        "SJR 120€/j, formule B domine",
        sjr=120, age=45, jours=400,
        attendu_jour=68.40, attendu_mois=2081.0,
    ))

    # SJR 200 — gros salaire, formule B, plafond 70% non atteint
    resultats.append(_test(
        "SJR 200€/j, gros salaire non plafonné",
        sjr=200, age=38, jours=300,
        attendu_jour=114.0, attendu_mois=3468.0,
    ))

    # SJR 300 — formule B = 171, plafond 70% = 210 (non atteint ; 57% < 70% par construction)
    resultats.append(_test(
        "SJR 300€/j, nouveau régime, plafond non atteint",
        sjr=300, age=50, jours=548,
        attendu_jour=171.0, attendu_mois=5202.0,
    ))

    # --- Ancien régime (avant avril 2025, plafond 75%) ---

    # Même résultat numérique — le plafond 75% n'est pas plus contraignant que le plafond 70%
    # pour la formule B (57%). Le flag vérifie le bon câblage du paramètre.
    resultats.append(_test(
        "SJR 300€/j, ancien régime (75%), résultat identique",
        sjr=300, age=45, jours=548,
        fin_contrat_avant_reforme=True,
        attendu_jour=171.0, attendu_mois=5202.0,
    ))

    # --- Durées selon l'âge ---

    resultats.append(_test(
        "SJR 80€/j, 54 ans, durée max 548j",
        sjr=80, age=54, jours=700,
        attendu_jour=45.60, attendu_mois=1387.0,
    ))

    resultats.append(_test(
        "SJR 80€/j, 56 ans, durée max 685j",
        sjr=80, age=56, jours=700,
        attendu_jour=45.60, attendu_mois=1387.0,
    ))

    resultats.append(_test(
        "SJR 80€/j, 57 ans, durée max 822j",
        sjr=80, age=57, jours=900,
        attendu_jour=45.60, attendu_mois=1387.0,
    ))

    # --- Vérifications internes ---
    print()
    print("  Vérifications internes :")

    params = _charger_parametres()

    assert params["partie_fixe"] == 13.18, f"Partie fixe attendue 13,18 — reçu {params['partie_fixe']}"
    assert params["plancher_journalier"] == 32.13, f"Plancher attendu 32,13 — reçu {params['plancher_journalier']}"
    assert params["plafond_nouveau"] == 0.70, f"Plafond nouveau régime attendu 70% — reçu {params['plafond_nouveau']}"
    assert params["plafond_ancien"] == 0.75, f"Plafond ancien régime attendu 75% — reçu {params['plafond_ancien']}"
    assert params["arce_pct"] == 0.60, f"ARCE attendu 60% — reçu {params['arce_pct']}"
    print("  ✓  Paramètres : partie fixe=13,18€, plancher=32,13€, plafonds 70%/75%, ARCE=60%")

    assert _duree_max(40, params) == 548
    assert _duree_max(55, params) == 685
    assert _duree_max(56, params) == 685
    assert _duree_max(57, params) == 822
    assert _duree_max(70, params) == 822
    print("  ✓  Durées max : <55→548j, 55-56→685j, ≥57→822j")

    # ARE jamais inférieure au plancher (sans activité réduite)
    for sjr_test in [5, 15, 30, 32, 33]:
        r = calcul_are(sjr_test, 40, 365)
        assert r["are_nette_journaliere"] >= params["plancher_journalier"], (
            f"ARE < plancher pour SJR={sjr_test}"
        )
    print("  ✓  Plancher garanti pour tous les SJR testés")

    # Monotonicité : ARE augmente avec le SJR (au-delà du plancher)
    prev = 0.0
    for sjr_test in [40, 60, 80, 120, 200]:
        r = calcul_are(sjr_test, 40, 365)
        assert r["are_nette_journaliere"] >= prev, f"ARE non monotone à SJR={sjr_test}"
        prev = r["are_nette_journaliere"]
    print("  ✓  Monotonicité : ARE croissante avec le SJR")

    # ARCE = 60% × droits_restants × ARE/j
    r = calcul_are(80, 42, 365, droits_restants=100)
    capital_attendu = round(0.60 * 100 * r["are_nette_journaliere"], 2)
    assert r["arce"]["capital_total"] == capital_attendu, (
        f"ARCE incorrecte : attendu {capital_attendu}, reçu {r['arce']['capital_total']}"
    )
    print("  ✓  ARCE : capital = 60% × droits_restants × ARE journalière")

    # --- Tests de bornes (property-based) ---
    print()
    print("  Tests de bornes :")

    # Continuité au croisement formule A (0.404 × SJR + 13.18) = formule B (0.57 × SJR).
    # Résolution : 13.18 = 0.166 × SJR → SJR croisement ≈ 79.40 €.
    # Autour du croisement, pas de saut visible (max de deux affines → C0).
    r1 = calcul_are(79.0, 40, 365)
    r2 = calcul_are(80.0, 40, 365)
    diff = r2["are_nette_journaliere"] - r1["are_nette_journaliere"]
    ok = 0.40 <= diff <= 0.60  # pente entre 0.404 (A) et 0.57 (B)
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Continuité croisement A/B (SJR 79→80) : Δ = {diff:.2f}€ "
          f"(attendu ∈ [0.40, 0.60])")

    # Marginalité formule A seule (avant croisement, SJR < 79.40) — pente 0.404.
    r1 = calcul_are(70.0, 40, 365)
    r2 = calcul_are(71.0, 40, 365)
    diff = r2["are_nette_journaliere"] - r1["are_nette_journaliere"]
    ok = abs(diff - 0.404) < 0.02
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Marginal formule A (SJR 70→71) : Δ = {diff:.3f}€ "
          f"(attendu ≈ 0.404)")

    # Marginalité formule B seule (après croisement, SJR > 79.40) — pente 0.57.
    r1 = calcul_are(150.0, 40, 365)
    r2 = calcul_are(151.0, 40, 365)
    diff = r2["are_nette_journaliere"] - r1["are_nette_journaliere"]
    ok = abs(diff - 0.57) < 0.02
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Marginal formule B (SJR 150→151) : Δ = {diff:.3f}€ "
          f"(attendu ≈ 0.57)")

    # Plancher — actif quand max(A, B) < 32.13 €, inactif au-dessus.
    # Seuil : formule A = 32.13 → SJR = (32.13 − 13.18) / 0.404 ≈ 46.90 €.
    r_bas = calcul_are(30.0, 40, 365)  # bien sous seuil → plancher
    r_haut = calcul_are(100.0, 40, 365)  # bien au-dessus → pas de plancher
    ok = r_bas["are_nette_journaliere"] == 32.13 and r_haut["are_nette_journaliere"] > 32.13
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Plancher : actif à SJR=30 ({r_bas['are_nette_journaliere']}€), "
          f"inactif à SJR=100 ({r_haut['are_nette_journaliere']}€)")

    # Plafond 70 % — jamais binding pour des SJR réalistes.
    # Formule B = 57 % × SJR < 70 % × SJR (toujours). Formule A = 40.4 % × SJR + 13.18
    # atteint 70 % × SJR quand SJR = 44.53 € ; mais sous ce seuil le plancher domine.
    for sjr_test in [50, 100, 500, 1000, 10000]:
        r = calcul_are(sjr_test, 40, 365)
        ok = r["are_nette_journaliere"] <= 0.70 * sjr_test + 0.01  # tolérance arrondi
        resultats.append(ok)
        if not ok:
            print(f"    ✗ ÉCHOUÉ  Plafond 70% dépassé à SJR={sjr_test} : "
                  f"ARE={r['are_nette_journaliere']}€ > 70%×SJR={0.70*sjr_test}€")
    print(f"    ✓  Plafond 70 % jamais binding (5 SJR testés de 50 à 10 000 €)")

    # Durée max à tous les seuils d'âge.
    for age_test, duree_att in [(30, 548), (54, 548), (55, 685), (56, 685),
                                  (57, 822), (70, 822)]:
        ok = _duree_max(age_test, params) == duree_att
        resultats.append(ok)
        if not ok:
            print(f"    ✗ ÉCHOUÉ  Durée âge {age_test} : "
                  f"attendu {duree_att}, reçu {_duree_max(age_test, params)}")
    print(f"    ✓  Durées aux 6 âges seuils (30, 54, 55, 56, 57, 70)")

    # Cumul activité réduite — monotonie : plus le revenu activité augmente,
    # moins l'ARE payable (jamais négative).
    r_0 = calcul_are(100, 40, 365, cumul_activite_reduite=0)
    r_500 = calcul_are(100, 40, 365, cumul_activite_reduite=500)
    r_1500 = calcul_are(100, 40, 365, cumul_activite_reduite=1500)
    r_5000 = calcul_are(100, 40, 365, cumul_activite_reduite=5000)
    a_0 = r_0["are_nette_journaliere"]
    a_500 = r_500["cumul_activite_reduite"]["are_journaliere_reduite"]
    a_1500 = r_1500["cumul_activite_reduite"]["are_journaliere_reduite"]
    a_5000 = r_5000["cumul_activite_reduite"]["are_journaliere_reduite"]
    ok = a_0 > a_500 > a_1500 >= 0 and a_5000 == 0
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Cumul activité : monotonie décroissante "
          f"({a_0}→{a_500}→{a_1500}→{a_5000})")

    # Cumul activité réduite — inégalité "pas perdant" : revenu_activité + ARE payable
    # ≥ ARE solo (reprendre une activité ne doit jamais diminuer le revenu total).
    r_solo = calcul_are(100, 40, 365)
    for revenu_act in [500, 1000, 2000, 3000]:
        r_cumul = calcul_are(100, 40, 365, cumul_activite_reduite=revenu_act)
        are_reduite_mensuelle = r_cumul["cumul_activite_reduite"]["are_mensuelle_reduite"]
        total_cumul = are_reduite_mensuelle + revenu_act
        ok = total_cumul >= r_solo["are_nette_mensuelle"]
        resultats.append(ok)
        if not ok:
            print(f"    ✗ ÉCHOUÉ  Cumul perdant à revenu={revenu_act} : "
                  f"total={total_cumul} < ARE solo={r_solo['are_nette_mensuelle']}")
    print(f"    ✓  Cumul : total (ARE payable + revenu activité) ≥ ARE solo (4 revenus)")

    # ARCE : avantage_arce_vs_maintien = -40 % × droits × ARE/j (exactement).
    # Sanity : ARCE = 60 % en cash, maintien = 100 % sur la durée, donc perte fixe 40 %.
    r = calcul_are(120, 45, 400, droits_restants=300)
    avantage_attendu = round(-0.40 * 300 * r["are_nette_journaliere"], 2)
    avantage_calcule = r["arce"]["avantage_arce_vs_maintien"]
    ok = abs(avantage_calcule - avantage_attendu) < 1.0
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  ARCE avantage = −40 % × droits × ARE/j : "
          f"calculé {avantage_calcule}€, attendu {avantage_attendu}€")

    # --- Résumé ---
    print()
    print("=" * 80)
    nb_ok = sum(resultats)
    nb_total = len(resultats)
    if nb_ok == nb_total:
        print(f"  ✓  {nb_ok}/{nb_total} cas OK — calcul_are.py prêt")
    else:
        nb_ko = nb_total - nb_ok
        print(f"  ✗  {nb_ko} cas ÉCHOUÉS sur {nb_total} — voir détails ci-dessus")
    print("=" * 80)
    print()

    return nb_ok == nb_total


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
