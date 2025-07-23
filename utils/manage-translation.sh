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

echo "✅ Translations à jour."
