"""
Tests pour calcul_ir.py — IR 2026 (revenus 2025).

Deux familles :
  1. Cas connus — valeurs à vérifier manuellement sur simulateur-ir.impots.gouv.fr.
     Voir `scripts/golden_cases_ir.md` pour la procédure (saisie → observation).
     Tant que `golden_cases_ir.md` n'est pas rempli, ces cas valident la cohérence
     interne du calculateur (non-régression), pas sa conformité au simulateur officiel.
  2. Tests de bornes — property-based : monotonicité, continuité aux seuils de
     tranche et de décote, plafonnement QF, marginalité. Pas de valeur "attendue"
     dérivée à la main (risque de copier une erreur de formule).

Hors scope : CEHR (CGI art. 223 sexies), crédits d'impôt, abattements spécifiques.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calcul_ir import calcul_ir, _load_bareme, _load_foyer

# Tolérance admise entre calcul et valeur de référence (€)
TOLERANCE = 5.0


def _test(desc, rni, parts, situation, ir_net_attendu):
    result = calcul_ir(rni, parts, situation)
    diff = abs(result["ir_net"] - ir_net_attendu)
    statut = "✓" if diff <= TOLERANCE else "✗ ÉCHOUÉ"
    print(
        f"  {statut}  {desc:<48}"
        f"  attendu {ir_net_attendu:>7,.0f}€"
        f"  calculé {result['ir_net']:>7,.0f}€"
        f"  (Δ {diff:.0f}€)"
    )
    return diff <= TOLERANCE


def main():
    print()
    print("=" * 72)
    print("  TESTS calcul_ir.py — IR 2026 (revenus 2025)")
    print("=" * 72)

    resultats = []

    # --- Cas célibataire ---

    # Valeurs recalculées le 2026-04-23 après correction du barème dans
    # ir_2026.json (tranches passées de 11 497/29 315/83 823/180 294 —
    # valeurs 2025 — aux vraies valeurs 2026 : 11 600/29 579/84 577/181 917).
    # Cross-checked via Service-Public.gouv.fr/particuliers/vosdroits/F1419.

    # RNI nul → IR nul
    resultats.append(_test(
        "Célibataire, RNI 0€",
        rni=0, parts=1.0, situation="celibataire",
        ir_net_attendu=0,
    ))

    # Revenus très faibles — décote efface tout
    resultats.append(_test(
        "Célibataire, RNI 14 000€ (décote → 0)",
        rni=14000, parts=1.0, situation="celibataire",
        ir_net_attendu=0,
    ))

    # Juste au-dessus du seuil de décote. IR brut = 924 ; décote = 897 − 0.4525×924 = 478.89 ; net = 445.
    resultats.append(_test(
        "Célibataire, RNI 20 000€ (décote partielle)",
        rni=20000, parts=1.0, situation="celibataire",
        ir_net_attendu=445,
    ))

    # Cas standard — tranche 11% + 30%. 17979×0.11 + 15421×0.30 = 6603.99.
    resultats.append(_test(
        "Célibataire, RNI 45 000€",
        rni=45000, parts=1.0, situation="celibataire",
        ir_net_attendu=6604,
    ))

    # Tranche 30%. 17979×0.11 + 5421×0.30 = 3603.99.
    resultats.append(_test(
        "Célibataire, RNI 35 000€",
        rni=35000, parts=1.0, situation="celibataire",
        ir_net_attendu=3604,
    ))

    # Tranche 41%. 17979×0.11 + 54998×0.30 + 15423×0.41 = 24800.52.
    resultats.append(_test(
        "Célibataire, RNI 100 000€ (tranche 41%)",
        rni=100000, parts=1.0, situation="celibataire",
        ir_net_attendu=24801,
    ))

    # Tranche 45%. 17979×0.11 + 54998×0.30 + 97340×0.41 + 18083×0.45 = 66523.84.
    resultats.append(_test(
        "Célibataire, RNI 200 000€ (tranche 45%)",
        rni=200000, parts=1.0, situation="celibataire",
        ir_net_attendu=66524,
    ))

    # --- Cas couple sans enfant ---

    # Couple, faibles revenus — décote couple
    resultats.append(_test(
        "Couple, RNI 30 000€ (décote couple)",
        rni=30000, parts=2.0, situation="couple",
        ir_net_attendu=0,
    ))

    # Couple standard. Par part 30k → 1977.69 + 421×0.30 = 2103.99. ×2 = 4207.98.
    resultats.append(_test(
        "Couple, RNI 60 000€",
        rni=60000, parts=2.0, situation="couple",
        ir_net_attendu=4208,
    ))

    # Par part 40k → 1977.69 + 10421×0.30 = 5103.99. ×2 = 10207.98.
    resultats.append(_test(
        "Couple, RNI 80 000€",
        rni=80000, parts=2.0, situation="couple",
        ir_net_attendu=10208,
    ))

    # --- Cas avec enfants (quotient familial) ---

    # 1 enfant = +0.5 part → plafond 1 807€ par demi-part.
    # 2.5p : par part 28k → (28000-11600)×0.11 = 1804. ×2.5 = 4510.
    # 2p ref : par part 35k → 3603.99. ×2 = 7207.98. Gain QF 2697.98 > plafond 1807 → plafonné.
    # Résultat : 7207.98 − 1807 = 5400.98.
    resultats.append(_test(
        "Couple + 1 enfant (2.5 parts), RNI 70 000€",
        rni=70000, parts=2.5, situation="couple",
        ir_net_attendu=5401,
    ))

    # 2 enfants = +1 part → plafond 3 614€ (2 × 1 807€).
    # 3p : par part 26666.67 → (26666.67-11600)×0.11 = 1657.33. ×3 = 4971.99.
    # 2p ref : 10207.98. Gain 5236 > 3614 → plafonné : 10207.98 − 3614 = 6593.98.
    resultats.append(_test(
        "Couple + 2 enfants (3 parts), RNI 80 000€",
        rni=80000, parts=3.0, situation="couple",
        ir_net_attendu=6594,
    ))

    # Plafonnement QF (revenus élevés).
    # 3p : par part 66666.67 → 1977.69 + 37087.67×0.30 = 13103.99. ×3 = 39311.97.
    # 2p ref : par part 100k → 24800.52. ×2 = 49601.04. Plafonné : 49601.04 − 3614 = 45987.04.
    resultats.append(_test(
        "Couple + 2 enfants (3 parts), RNI 200 000€ (QF plafonné)",
        rni=200000, parts=3.0, situation="couple",
        ir_net_attendu=45987,
    ))

    # --- Vérifications internes ---
    print()
    print("  Vérifications internes :")

    # Le barème charge correctement
    tranches, decote, qf = _load_bareme()
    assert len(tranches) == 5, f"5 tranches attendues, {len(tranches)} chargées"
    assert tranches[0]["rate"] == 0.0
    assert tranches[1]["rate"] == 0.11
    assert tranches[2]["rate"] == 0.30
    assert tranches[3]["rate"] == 0.41
    assert tranches[4]["rate"] == 0.45
    print("  ✓  Barème : 5 tranches chargées (0%, 11%, 30%, 41%, 45%)")

    assert decote["celibataire"]["seuil_impot_brut"] == 1982
    assert decote["couple"]["seuil_impot_brut"] == 3277
    print("  ✓  Décote : seuils célibataire=1 982€, couple=3 277€")

    # IR net jamais négatif
    for rni_test in [0, 1000, 50000, 500000]:
        r = calcul_ir(rni_test, 1.0, "celibataire")
        assert r["ir_net"] >= 0, f"IR négatif pour RNI={rni_test}"
    print("  ✓  IR net ≥ 0 pour tous les cas testés")

    # Monotonicité : IR augmente avec le RNI
    prev = 0.0
    for rni_test in [20000, 30000, 50000, 100000]:
        r = calcul_ir(rni_test, 1.0, "celibataire")
        assert r["ir_net"] >= prev, f"IR non monotone à RNI={rni_test}"
        prev = r["ir_net"]
    print("  ✓  Monotonicité : IR croissant avec le RNI")

    # --- Tests de bornes (property-based) ---
    print()
    print("  Tests de bornes :")

    # Continuité aux 4 seuils de tranche — pas de saut visible autour du seuil.
    # IR(seuil+1) − IR(seuil−1) doit être petit (2 × taux marginal max = 0.9 €).
    for seuil in [11600, 29579, 84577, 181917]:
        r_avant = calcul_ir(seuil - 1, 1.0, "celibataire")
        r_apres = calcul_ir(seuil + 1, 1.0, "celibataire")
        diff = r_apres["ir_brut_total"] - r_avant["ir_brut_total"]
        ok = 0 <= diff <= 1.0
        resultats.append(ok)
        statut = "✓" if ok else "✗ ÉCHOUÉ"
        print(f"    {statut}  Continuité seuil {seuil:>7,}€ : Δ = {diff:>5.2f}€")

    # Marginalité — dans une tranche, IR(x+1000) − IR(x) ≈ 1000 × taux_marginal.
    for rni, rate in [(50000, 0.30), (100000, 0.41), (250000, 0.45)]:
        r1 = calcul_ir(rni, 1.0, "celibataire")
        r2 = calcul_ir(rni + 1000, 1.0, "celibataire")
        marginal = r2["ir_brut_total"] - r1["ir_brut_total"]
        attendu = 1000 * rate
        ok = abs(marginal - attendu) < 1.0
        resultats.append(ok)
        statut = "✓" if ok else "✗ ÉCHOUÉ"
        print(f"    {statut}  Marginal tranche {rate*100:>2.0f}% à RNI={rni:>6,}€ : "
              f"{marginal:>6.2f}€ (attendu ≈ {attendu:.0f}€)")

    # Décote — active sous le seuil d'impôt brut, nulle au-dessus.
    # RNI 29 000 → ir_brut ≈ 1 945 € (< 1 983) → décote appliquée.
    # RNI 30 000 → ir_brut ≈ 2 055 € (> 1 983) → décote = 0.
    r_bas = calcul_ir(29000, 1.0, "celibataire")
    r_haut = calcul_ir(30000, 1.0, "celibataire")
    ok = r_bas["decote_appliquee"] > 0 and r_haut["decote_appliquee"] == 0
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Décote : active <seuil ({r_bas['decote_appliquee']:.0f}€), "
          f"nulle >seuil ({r_haut['decote_appliquee']:.0f}€)")

    # Plafonnement QF — couple + 2 enfants : non plafonné à RNI modeste, plafonné à RNI élevé.
    r_bas = calcul_ir(50000, 3.0, "couple")
    r_haut = calcul_ir(200000, 3.0, "couple")
    ok = not r_bas["qf_plafonne"] and r_haut["qf_plafonne"]
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  QF : non plafonné à RNI=50k, plafonné à RNI=200k (couple + 2 enf.)")

    # Progressivité — doubler le revenu plus que double l'impôt (tranches supérieures).
    r_x = calcul_ir(30000, 1.0, "celibataire")
    r_2x = calcul_ir(60000, 1.0, "celibataire")
    ok = r_2x["ir_net"] > 2 * r_x["ir_net"]
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Progressivité : IR(60k)={r_2x['ir_net']:,.0f}€ > "
          f"2×IR(30k)={2*r_x['ir_net']:,.0f}€")

    # Taux moyen < TMI — même à revenus extrêmes, le taux moyen reste < 45 %.
    r = calcul_ir(10_000_000, 1.0, "celibataire")
    ok = r["ir_net"] >= 0 and r["taux_moyen"] < 45.0
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  IR(10 M€) : ir_net={r['ir_net']:,.0f}€, "
          f"taux_moyen={r['taux_moyen']:.2f}% (< 45 %)")

    # --- Résumé ---
    print()
    print("=" * 72)
    nb_ok = sum(resultats)
    nb_total = len(resultats)
    if nb_ok == nb_total:
        print(f"  ✓  {nb_ok}/{nb_total} cas OK — calcul_ir.py prêt")
    else:
        nb_ko = nb_total - nb_ok
        print(f"  ✗  {nb_ko} cas ÉCHOUÉS sur {nb_total} — voir détails ci-dessus")
    print("=" * 72)
    print()

    return nb_ok == nb_total


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
