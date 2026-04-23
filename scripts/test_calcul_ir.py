"""
Tests unitaires pour calcul_ir.py — cas connus IR 2026 (revenus 2025)

Tolérance : ±5 € sur l'IR net (arrondi + estimations barème).
Chaque cas est vérifiable sur le simulateur impots.gouv.fr.
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

    # Juste au-dessus du seuil de décote
    resultats.append(_test(
        "Célibataire, RNI 20 000€ (décote partielle)",
        rni=20000, parts=1.0, situation="celibataire",
        ir_net_attendu=462,
    ))

    # Cas standard — tranche 11% + 30%
    resultats.append(_test(
        "Célibataire, RNI 45 000€",
        rni=45000, parts=1.0, situation="celibataire",
        ir_net_attendu=6665,
    ))

    # Tranche 30%
    resultats.append(_test(
        "Célibataire, RNI 35 000€",
        rni=35000, parts=1.0, situation="celibataire",
        ir_net_attendu=3665,
    ))

    # Tranche 41%
    resultats.append(_test(
        "Célibataire, RNI 100 000€ (tranche 41%)",
        rni=100000, parts=1.0, situation="celibataire",
        ir_net_attendu=24945,
    ))

    # Tranche 45%
    resultats.append(_test(
        "Célibataire, RNI 200 000€ (tranche 45%)",
        rni=200000, parts=1.0, situation="celibataire",
        ir_net_attendu=66733,
    ))

    # --- Cas couple sans enfant ---

    # Couple, faibles revenus — décote couple
    resultats.append(_test(
        "Couple, RNI 30 000€ (décote couple)",
        rni=30000, parts=2.0, situation="couple",
        ir_net_attendu=0,
    ))

    # Couple standard
    resultats.append(_test(
        "Couple, RNI 60 000€",
        rni=60000, parts=2.0, situation="couple",
        ir_net_attendu=4331,
    ))

    resultats.append(_test(
        "Couple, RNI 80 000€",
        rni=80000, parts=2.0, situation="couple",
        ir_net_attendu=10331,
    ))

    # --- Cas avec enfants (quotient familial) ---

    # 1 enfant = +0.5 part → plafond 1 807€ par demi-part
    resultats.append(_test(
        "Couple + 1 enfant (2.5 parts), RNI 70 000€",
        rni=70000, parts=2.5, situation="couple",
        ir_net_attendu=5524,
    ))

    # 2 enfants = +1 part → plafond 3 614€ (2 × 1 807€)
    resultats.append(_test(
        "Couple + 2 enfants (3 parts), RNI 80 000€",
        rni=80000, parts=3.0, situation="couple",
        ir_net_attendu=6717,
    ))

    # Plafonnement QF (revenus élevés)
    resultats.append(_test(
        "Couple + 2 enfants (3 parts), RNI 200 000€ (QF plafonné)",
        rni=200000, parts=3.0, situation="couple",
        ir_net_attendu=46276,
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

    assert decote["celibataire"]["seuil_impot_brut"] == 1983
    assert decote["couple"]["seuil_impot_brut"] == 3278
    print("  ✓  Décote : seuils célibataire=1 983€, couple=3 278€")

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
