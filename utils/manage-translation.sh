#!/bin/bash
set -e

# 📍 Configuration
LOCALES=("fr" "en")
DOMAIN="messages"
TRANSLATION_DIR="translations"
BABEL_CFG="babel.cfg"
POT_FILE="messages.pot"

cd ../app || exit 1

echo "🔄 Extraction des messages..."
pybabel extract -F "$BABEL_CFG" -o "$POT_FILE" .

echo "🆕 Mise à jour ou création des traductions..."
for locale in "${LOCALES[@]}"; do
  PO_FILE="$TRANSLATION_DIR/$locale/LC_MESSAGES/$DOMAIN.po"
  if [ -f "$PO_FILE" ]; then
    echo "✅ Mise à jour pour '$locale'"
    pybabel update -i "$POT_FILE" -d "$TRANSLATION_DIR" -l "$locale"
  else
    echo "➕ Initialisation de la langue '$locale'"
    pybabel init -i "$POT_FILE" -d "$TRANSLATION_DIR" -l "$locale"
  fi
done

echo "⚙️ Compilation des traductions..."
pybabel compile -d "$TRANSLATION_DIR"

echo "🧹 Nettoyage du fichier modèle..."
rm -f "$POT_FILE"

echo "🔎 Vérification des traductions manquantes..."
# Vérifie la présence des outils gettext utiles
if ! command -v msgfmt >/dev/null 2>&1; then
  echo "⚠️  'msgfmt' (gettext) est introuvable. Impossible d'afficher les statistiques."
fi
if ! command -v msggrep >/dev/null 2>&1 && ! command -v msgattrib >/dev/null 2>&1; then
  echo "⚠️  'msggrep' et 'msgattrib' sont introuvables. Impossible de lister les chaînes manquantes."
fi

for locale in "${LOCALES[@]}"; do
  PO_FILE="$TRANSLATION_DIR/$locale/LC_MESSAGES/$DOMAIN.po"
  echo
  echo "=== 🌐 $locale ==="

  # 1) Statistiques (traduites / fuzzy / non traduites)
  if command -v msgfmt >/dev/null 2>&1; then
    # Supprime la sortie binaire, on ne garde que les stats sur stderr
    STATS=$(msgfmt --statistics -o /dev/null "$PO_FILE" 2>&1 || true)
    echo "📊 $STATS"
  fi

  # 2) Liste des msgid non traduits
  #    Priorité à msggrep; sinon fallback avec msgattrib; sinon fallback très basique avec grep.
   # 2) Liste des msgid non traduits
  if command -v msgattrib >/dev/null 2>&1; then
    MISSING=$(msgattrib --untranslated --no-obsolete "$PO_FILE" | sed -n '/^msgid /,/^$/p' | awk '
      BEGIN{RS=""; ORS="\n\n"}
      $0 !~ /\nmsgid ""\n/ {print}')
  else
    # Fallback basique si pas de msgattrib
    MISSING=$(awk -v RS='' '/\nmsgstr ""(\n|$)/{print}' "$PO_FILE" | sed -n '/^msgid /,/^$/p' | awk '
      BEGIN{RS=""; ORS="\n\n"}
      $0 !~ /\nmsgid ""\n/ {print}')
  fi

  if [ -n "$MISSING" ]; then
    echo "❗ Chaînes non traduites :"
    # Affiche proprement les msgid (et msgid_plural s’il y en a)
    echo "$MISSING" | awk '
      BEGIN{RS=""; ORS="\n\n"; FS="\n"}
      {
        id=""; plural=""
        for (i=1;i<=NF;i++){
          if ($i ~ /^msgid "/) {id = $i}
          if ($i ~ /^msgid_plural "/) {plural = $i}
        }
        if (id != "") {
          print id
          if (plural != "") print plural
        }
      }'
  else
    echo "✅ Aucune chaîne manquante."
  fi
done

echo
echo "✅ Translations à jour."
