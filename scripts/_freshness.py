"""
Contrôle de fraîcheur partagé pour les scripts Marcel.

Point unique de vérité : les règles fiscales/sociales changent au 1er janvier
(loi de finances). Tout fichier *_2026.json dont `_meta.derniere_verification`
est antérieure au 1er janvier de l'année courante déclenche une alerte stderr
avant que le calcul ne produise un résultat.

Pattern : chaque calcul_*.py appelle `check_freshness(data, "xxx_2026.json")`
au chargement de ses paramètres, avant la première utilisation.
"""

import sys
from datetime import date


def fraicheur_seuil() -> date:
    """
    Seuil de fraîcheur = 1er janvier de l'année courante.

    Dynamique — sinon un seuil hardcodé `date(2026, 1, 1)` rend l'alerte muette
    dès le 1er janvier 2027, silencieusement, pour toujours.
    """
    return date(date.today().year, 1, 1)


def check_freshness(data: dict, source_name: str) -> None:
    """
    Alerte stderr si `data["_meta"]["derniere_verification"]` est périmée,
    absente, ou malformée.

    Silence si la date est ≥ seuil (1er janvier année courante).

    Cas couverts :
      - date manquante → alerte "pas de date de vérification"
      - date non ISO  → alerte "date invalide"
      - date < seuil  → alerte "vérifié le X, avant le seuil Y"
      - date ≥ seuil  → silence
    """
    verif_str = data.get("_meta", {}).get("derniere_verification")
    if not verif_str:
        print(f"⚠️  Fraîcheur : pas de date de vérification dans {source_name}",
              file=sys.stderr)
        return
    try:
        verif = date.fromisoformat(verif_str)
    except ValueError:
        print(f"⚠️  Fraîcheur : date invalide '{verif_str}' dans {source_name}",
              file=sys.stderr)
        return
    seuil = fraicheur_seuil()
    if verif < seuil:
        print(f"⚠️  Fraîcheur : {source_name} vérifié le {verif}, avant le seuil "
              f"{seuil}. Règles peut-être périmées — relance "
              f"`mettre-a-jour-taux` avant de te fier au calcul.",
              file=sys.stderr)
