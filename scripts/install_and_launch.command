#!/usr/bin/env bash
# ==============================================================================
# 1-Click Installer & Permission Fixer for Remon AI Background Remover Pro
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_NAME="Remon AI Background Remover Pro V 01.02.app"
DEST="/Applications/${APP_NAME}"

echo ""
echo "=================================================================="
echo "    Installing Remon AI Background Remover Pro V 01.02           "
echo "=================================================================="
echo ""

if [ ! -d "${DIR}/${APP_NAME}" ]; then
    echo "Error: ${APP_NAME} not found in DMG!"
    exit 1
fi

echo "[1/2] Copying application to /Applications..."
rm -rf "${DEST}"
cp -R "${DIR}/${APP_NAME}" "/Applications/"

echo "[2/2] Authorizing macOS permissions (bypassing Gatekeeper warning)..."
xattr -cr "${DEST}" 2>/dev/null || true
xattr -d com.apple.quarantine "${DEST}" 2>/dev/null || true

echo ""
echo "=================================================================="
echo " Installation Complete! Launching application now...              "
echo "=================================================================="
echo ""

open "${DEST}"
sleep 1
exit 0
