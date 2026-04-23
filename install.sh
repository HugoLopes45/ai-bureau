#!/usr/bin/env bash
# install.sh — Setup Marcel dans ton répertoire courant.
#
# Idempotent : peut être relancé autant de fois que tu veux.
# NE JAMAIS écraser foyer.json ou patrimoine.json existants (règle dure —
# ces fichiers contiennent tes données fiscales réelles).
#
# Usage :
#   ./install.sh              # setup dans le répertoire courant
#   ./install.sh --check      # vérifie seulement les prérequis

set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_ONLY=0

# --- Arguments ---
for arg in "$@"; do
    case "$arg" in
        --check) CHECK_ONLY=1 ;;
        -h|--help)
            sed -n '2,10p' "$0" | sed 's/^# //;s/^#//'
            exit 0
            ;;
        *) echo "Option inconnue : $arg" >&2; exit 1 ;;
    esac
done

# --- Helpers ---
green() { printf '\033[32m%s\033[0m\n' "$1"; }
yellow() { printf '\033[33m%s\033[0m\n' "$1"; }
red() { printf '\033[31m%s\033[0m\n' "$1"; }

echo
echo "Marcel — Installation"
echo "====================="
echo

# --- Prérequis ---
missing=0

if ! command -v python3 >/dev/null 2>&1; then
    red "✗ python3 non trouvé"
    echo "  Installe Python 3.8+ : https://www.python.org/downloads/"
    missing=1
else
    py_version=$(python3 --version 2>&1 | awk '{print $2}')
    green "✓ python3 $py_version"
fi

if ! command -v claude >/dev/null 2>&1; then
    yellow "⚠  claude (CLI Claude Code) non trouvé dans le PATH"
    echo "  Installe Claude Code : https://claude.com/download"
    echo "  (pas bloquant si tu utilises claude.ai/code ou l'extension IDE)"
else
    green "✓ claude CLI présent"
fi

if [ "$missing" -eq 1 ]; then
    red "Prérequis manquants — installe-les puis relance ./install.sh"
    exit 1
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
    echo
    green "Vérification OK — lance sans --check pour créer les fichiers de config."
    exit 0
fi

echo

# --- Création des fichiers de config (jamais clobber) ---
copy_if_absent() {
    local src="$1"
    local dst="$2"
    if [ -f "$dst" ]; then
        yellow "· $dst existe déjà — pas touché (données potentiellement réelles)"
    elif [ ! -f "$src" ]; then
        red "✗ Template source introuvable : $src"
        exit 1
    else
        cp "$src" "$dst"
        green "✓ $dst créé depuis $src"
    fi
}

copy_if_absent "$ROOT/configs/foyer.example.json" "$ROOT/foyer.json"
copy_if_absent "$ROOT/configs/patrimoine.example.json" "$ROOT/patrimoine.json"

# --- Vérif rapide que les scripts marchent ---
echo
if python3 "$ROOT/scripts/calcul_ir.py" --rni 45000 --parts 1 --json >/dev/null 2>&1; then
    green "✓ scripts/calcul_ir.py fonctionne"
else
    red "✗ scripts/calcul_ir.py échoue — vérifie data/rates/ir_2026.json"
    exit 1
fi

# --- Message final ---
echo
green "Marcel est prêt."
echo
echo "Prochaine étape :"
echo "  1. Ouvre Claude Code dans ce répertoire."
echo "  2. Tape : /bonjour"
echo "     (Marcel te guidera selon ta question — impôts, retraite, logement, etc.)"
echo
echo "Tes données fiscales personnelles vivent dans :"
echo "  $ROOT/foyer.json"
echo "  $ROOT/patrimoine.json"
echo "(Gitignorés — ne quittent jamais ta machine sauf via Claude vers Anthropic."
echo " Détails du flux : DISCLAIMER.md §3.)"
echo
yellow "⚠️  Avant d'utiliser Marcel — important"
echo "  • Marcel est un outil d'information généré par IA, pas un conseil réglementé."
echo "  • Les chiffres peuvent être incorrects ou obsolètes — vérifie les sources officielles."
echo "  • Pour toute décision importante, consulte un pro agréé :"
echo "      impôts    → expert-comptable / avocat fiscaliste"
echo "      succession → notaire (consultation obligatoire > 5 k€)"
echo "      crédit    → courtier IOBSP (agréé ORIAS)"
echo "      placement → CIF agréé AMF"
echo "  • Cadre légal complet (RGPD, AI Act, licence, responsabilité) : $ROOT/DISCLAIMER.md"
echo
