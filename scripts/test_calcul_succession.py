"""
Tests pour calcul_succession.py — droits de succession 2026.

Deux familles :
  1. Cas connus — valeurs calculées à la main depuis le barème DGFiP (CGI art. 777
     et 779). À vérifier ensuite contre les exemples impots.gouv.fr (voir
     `golden_cases_succession.md`) ou openfisca-france.
  2. Tests de bornes — property-based : continuité aux 6 seuils ligne directe et
     au seuil frère/sœur, marginalité par tranche, monotonicité, exonération
     conjoint, cumul handicap, rappel fiscal 15 ans.

Hors scope : démembrement (CGI art. 669), assurance-vie (art. 990 I, 757 B),
Pacte Dutreil (art. 787 B), dons spéciaux (art. 790 G, don logement temp.),
partage civil entre cohéritiers (réserves).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from calcul_succession import calcul_succession, _charger_parametres


TOLERANCE = 1.0  # €


def _test(desc, actif, lien, attendu, **kwargs):
    r = calcul_succession(actif_recu=actif, lien_parente=lien, **kwargs)
    diff = abs(r["droits"] - attendu)
    ok = diff <= TOLERANCE
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(
        f"  {statut}  {desc:<52}"
        f"  attendu {attendu:>10,.0f}€"
        f"  calculé {r['droits']:>10,.0f}€"
        f"  (Δ {diff:.0f}€)"
    )
    return ok


def main():
    print()
    print("=" * 82)
    print("  TESTS calcul_succession.py — successions 2026")
    print("=" * 82)

    resultats = []

    # --- Cas ligne directe (enfant, petit-enfant, parent) ---

    # Enfant reçoit 300 000 € (canonique) :
    #   abattement 100 000 → base 200 000
    #     0→8072       × 5 %  =    403,60 €
    #     8072→12109   × 10 % =    403,70 €
    #     12109→15932  × 15 % =    573,45 €
    #     15932→200000 × 20 % = 36 813,60 €
    #   → 38 194 €
    resultats.append(_test(
        "Enfant, 300 000€ (tranche 20 %)",
        actif=300000, lien="enfant", attendu=38194,
    ))

    # Enfant reçoit 800 000 € → tranche 30 % activée
    #   abattement 100 000 → base 700 000
    #     0→8072       × 5 %  =       403,60 €
    #     8072→12109   × 10 % =       403,70 €
    #     12109→15932  × 15 % =       573,45 €
    #     15932→552324 × 20 % = 107 278,40 €
    #     552324→700000× 30 % =  44 302,80 €
    #   → 152 962 €
    resultats.append(_test(
        "Enfant, 800 000€ (tranche 30 % activée)",
        actif=800000, lien="enfant", attendu=152962,
    ))

    # Petit-enfant reçoit 50 000 €
    #   abattement 31 865 → base 18 135
    #   droits = 403,60 + 403,70 + 573,45 + 440,60 = 1 821 €
    resultats.append(_test(
        "Petit-enfant, 50 000€",
        actif=50000, lien="petit_enfant", attendu=1821,
    ))

    # --- Cas conjoint / PACS : exonération totale ---

    resultats.append(_test(
        "Conjoint, 1 000 000€ (exonération totale TEPA)",
        actif=1_000_000, lien="conjoint", attendu=0,
    ))

    # --- Cas frère/sœur ---

    # Frère/sœur reçoit 50 000 €
    #   abattement 15 932 → base 34 068
    #   0→24430 × 35 % = 8 550,50
    #   24430→34068 × 45 % = 4 337,10
    #   → 12 888 €
    resultats.append(_test(
        "Frère/sœur, 50 000€",
        actif=50000, lien="frere_soeur", attendu=12888,
    ))

    # --- Cas forfaitaires ---

    # Neveu/nièce reçoit 50 000 € → abattement 7 967, taux 55 %
    # (50000 − 7967) × 0.55 = 23 118
    resultats.append(_test(
        "Neveu/nièce, 50 000€ (forfait 55 %)",
        actif=50000, lien="neveu_niece", attendu=23118,
    ))

    # Non-parent reçoit 100 000 € → abattement 1 594, taux 60 %
    # (100000 − 1594) × 0.60 = 59 044
    resultats.append(_test(
        "Non-parent, 100 000€ (forfait 60 %)",
        actif=100000, lien="non_parent", attendu=59044,
    ))

    # --- Cas handicapé ---

    # Enfant handicapé reçoit 300 000 €
    #   abattement 100 000 + 159 325 = 259 325 → base 40 675
    #   403,60 + 403,70 + 573,45 + 24743 × 20 % = 6 329 €
    resultats.append(_test(
        "Enfant handicapé, 300 000€ (abattement 259 325 €)",
        actif=300000, lien="enfant", handicape=True, attendu=6329,
    ))

    # --- Cas rappel fiscal 15 ans (CGI art. 784) ---

    # Enfant reçoit 300 000 € mais a reçu 60 000 € en donation il y a 5 ans
    #   abattement résiduel = 100 000 − 60 000 = 40 000 → base 260 000
    #   403,60 + 403,70 + 573,45 + 244068 × 20 % = 50 194 €
    resultats.append(_test(
        "Enfant, 300 000€ avec donation 60 000€ récente",
        actif=300000, lien="enfant", donations_15_ans=60000, attendu=50194,
    ))

    # --- Vérifications internes ---
    print()
    print("  Vérifications internes :")

    params = _charger_parametres()
    abat = params["abattements"]

    assert abat["enfant"] == 100_000
    assert abat["petit_enfant"] == 31_865
    assert abat["frere_soeur"] == 15_932
    assert abat["neveu_niece"] == 7_967
    assert abat["autres"] == 1_594
    assert abat["handicape_bonus"] == 159_325
    print(f"  ✓  Abattements art. 779 : enfant 100 k, PE 31 865, F/S 15 932, "
          f"neveu 7 967, autres 1 594, handicapé +159 325")

    assert len(params["bareme_ligne_directe"]) == 7, \
        f"7 tranches ligne directe attendues, {len(params['bareme_ligne_directe'])} chargées"
    rates = [t["rate"] for t in params["bareme_ligne_directe"]]
    assert rates == [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.45]
    print("  ✓  Barème ligne directe : 7 tranches (5, 10, 15, 20, 30, 40, 45 %)")

    assert len(params["bareme_frere_soeur"]) == 2
    assert [t["rate"] for t in params["bareme_frere_soeur"]] == [0.35, 0.45]
    print("  ✓  Barème frère/sœur : 2 tranches (35 %, 45 %)")

    assert params["taux_4e_degre"] == 0.55
    assert params["taux_non_parent"] == 0.60
    print("  ✓  Taux forfaitaires : 4e degré 55 %, non-parents 60 %")

    # Droits jamais négatifs pour tous les liens
    for lien in ["enfant", "petit_enfant", "frere_soeur", "neveu_niece", "non_parent"]:
        for actif_t in [0, 1000, 50000, 500000]:
            r = calcul_succession(actif_t, lien)
            assert r["droits"] >= 0, f"Droits négatifs pour {lien} à {actif_t}€"
    print("  ✓  Droits ≥ 0 pour toutes combinaisons testées")

    # --- Tests de bornes (property-based) ---
    print()
    print("  Tests de bornes :")

    # Continuité aux seuils de tranche ligne directe.
    # Base taxable = actif − 100 000 (abattement enfant). Pour tester un seuil
    # de base b, on utilise actif = b + 100 000.
    for seuil in [8072, 12109, 15932, 552324, 902838, 1805677]:
        r_avant = calcul_succession(seuil + 100_000 - 1, "enfant")
        r_apres = calcul_succession(seuil + 100_000 + 1, "enfant")
        diff = r_apres["droits"] - r_avant["droits"]
        ok = 0 <= diff <= 1.0  # max 2 × 0.45 € de diff à 1 € d'écart
        resultats.append(ok)
        statut = "✓" if ok else "✗ ÉCHOUÉ"
        print(f"    {statut}  Continuité seuil ligne directe {seuil:>9,}€ : Δ = {diff:.2f}€")

    # Continuité au seuil frère/sœur (24 430, après abattement 15 932).
    r_avant = calcul_succession(24430 + 15932 - 1, "frere_soeur")
    r_apres = calcul_succession(24430 + 15932 + 1, "frere_soeur")
    diff = r_apres["droits"] - r_avant["droits"]
    ok = 0 <= diff <= 1.0  # max 2 × 0.45 € à 1 € d'écart
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Continuité seuil frère/sœur 24 430€ : Δ = {diff:.2f}€")

    # Marginalité dans la tranche 20 % ligne directe (base 100 k à 200 k).
    # droits(actif+1000) − droits(actif) ≈ 200 € dans cette tranche.
    r1 = calcul_succession(200000, "enfant")  # base 100k, dans tranche 20 %
    r2 = calcul_succession(201000, "enfant")
    diff = r2["droits"] - r1["droits"]
    ok = abs(diff - 200) < 1.0
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Marginal tranche 20 % (enfant 200k→201k) : Δ = {diff:.2f}€ "
          f"(attendu ≈ 200€)")

    # Marginalité dans la tranche 30 % (base 552k à 902k).
    r1 = calcul_succession(700000, "enfant")  # base 600k, dans tranche 30 %
    r2 = calcul_succession(701000, "enfant")
    diff = r2["droits"] - r1["droits"]
    ok = abs(diff - 300) < 1.0
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Marginal tranche 30 % (enfant 700k→701k) : Δ = {diff:.2f}€ "
          f"(attendu ≈ 300€)")

    # Marginalité tranche 45 % (au-delà de 1 805 677 après abattement).
    r1 = calcul_succession(3_000_000, "enfant")  # base 2.9M, bien dans 45 %
    r2 = calcul_succession(3_001_000, "enfant")
    diff = r2["droits"] - r1["droits"]
    ok = abs(diff - 450) < 1.0
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Marginal tranche 45 % (enfant 3M→3.001M) : Δ = {diff:.2f}€ "
          f"(attendu ≈ 450€)")

    # Marginalité forfait 55 % (neveu).
    r1 = calcul_succession(100_000, "neveu_niece")
    r2 = calcul_succession(101_000, "neveu_niece")
    diff = r2["droits"] - r1["droits"]
    ok = abs(diff - 550) < 1.0
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Marginal forfait 55 % (neveu 100k→101k) : Δ = {diff:.2f}€ "
          f"(attendu ≈ 550€)")

    # Marginalité forfait 60 % (non-parent).
    r1 = calcul_succession(100_000, "non_parent")
    r2 = calcul_succession(101_000, "non_parent")
    diff = r2["droits"] - r1["droits"]
    ok = abs(diff - 600) < 1.0
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Marginal forfait 60 % (non-parent 100k→101k) : Δ = {diff:.2f}€ "
          f"(attendu ≈ 600€)")

    # Monotonicité : droits croissent avec l'actif reçu.
    prev = -1.0
    for actif_t in [0, 50000, 100000, 300000, 1_000_000, 5_000_000]:
        r = calcul_succession(actif_t, "enfant")
        ok_mono = r["droits"] >= prev
        if not ok_mono:
            resultats.append(False)
            print(f"    ✗ ÉCHOUÉ  Monotonicité brisée à actif={actif_t}")
            break
        prev = r["droits"]
    else:
        resultats.append(True)
        print(f"    ✓  Monotonicité enfant : droits croissants sur 6 actifs de 0 à 5 M€")

    # Conjoint : droits = 0 quel que soit l'actif.
    ok = all(calcul_succession(a, "conjoint")["droits"] == 0
             for a in [0, 100_000, 10_000_000])
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Conjoint exonéré quel que soit l'actif (3 montants)")

    # Handicap : à lien et actif égaux, droits(handicapé) ≤ droits(non handicapé).
    for lien in ["enfant", "petit_enfant", "frere_soeur"]:
        r_std = calcul_succession(300000, lien)
        r_hcp = calcul_succession(300000, lien, handicape=True)
        ok_hcp = r_hcp["droits"] <= r_std["droits"]
        resultats.append(ok_hcp)
        if not ok_hcp:
            print(f"    ✗ ÉCHOUÉ  Handicap pénalisant pour {lien}")
    print(f"    ✓  Handicap : droits(handicapé) ≤ droits(non handicapé), 3 liens")

    # Rappel fiscal épuisé : donations_15_ans ≥ abattement_base → base = actif.
    r = calcul_succession(300000, "enfant", donations_15_ans=150_000)
    # abattement résiduel = 0, base = 300 000
    # 0→8072: 403.60, 8072→12109: 403.70, 12109→15932: 573.45, 15932→300000: 56813.60
    # Total ≈ 58 194 €
    ok = abs(r["droits"] - 58194) < 2.0
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Rappel 15 ans épuisé : abattement résiduel = 0, "
          f"droits = {r['droits']:,.0f}€ (attendu ≈ 58 194 €)")

    # Taux moyen < taux marginal maximum (45 % ligne directe).
    r = calcul_succession(50_000_000, "enfant")  # très gros actif
    ok = r["taux_moyen"] < 45.0
    resultats.append(ok)
    statut = "✓" if ok else "✗ ÉCHOUÉ"
    print(f"    {statut}  Taux moyen < 45 % même à 50 M€ : {r['taux_moyen']:.2f} %")

    # --- Résumé ---
    print()
    print("=" * 82)
    nb_ok = sum(resultats)
    nb_total = len(resultats)
    if nb_ok == nb_total:
        print(f"  ✓  {nb_ok}/{nb_total} cas OK — calcul_succession.py prêt")
    else:
        nb_ko = nb_total - nb_ok
        print(f"  ✗  {nb_ko} cas ÉCHOUÉS sur {nb_total} — voir détails ci-dessus")
    print("=" * 82)
    print()

    return nb_ok == nb_total


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
