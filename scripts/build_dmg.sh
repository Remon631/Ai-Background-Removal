#!/usr/bin/env bash
set -e

APP_NAME="Remon AI Background Remover Pro V 01.02"
APP_BUNDLE="dist/${APP_NAME}.app"
DMG_NAME="Remon_AI_Background_Remover_Pro_V_01.02.dmg"
DMG_PATH="dist/${DMG_NAME}"
STAGING_DIR="dist/dmg_staging"

echo "=== Packaging ${APP_NAME} into macOS DMG ==="

if [ ! -d "${APP_BUNDLE}" ]; then
    echo "Error: Application bundle not found at ${APP_BUNDLE}."
    exit 1
fi

echo "1. Preparing staging directory..."
rm -rf "${STAGING_DIR}" "${DMG_PATH}"
mkdir -p "${STAGING_DIR}"

echo "1.1 Cleaning extended attributes and ad-hoc signing application bundle..."
xattr -cr "${APP_BUNDLE}" || true
codesign --force --deep --sign - "${APP_BUNDLE}" || true

echo "2. Copying application bundle..."
cp -R "${APP_BUNDLE}" "${STAGING_DIR}/"

echo "3. Creating /Applications shortcut..."
ln -s /Applications "${STAGING_DIR}/Applications"

echo "4. Adding 1-Click Installer & Permission Fixer..."
cp "scripts/install_and_launch.command" "${STAGING_DIR}/1-Click Install & Launch.command"
chmod +x "${STAGING_DIR}/1-Click Install & Launch.command"

echo "5. Creating Quick Instructions..."
cat << 'EOF' > "${STAGING_DIR}/How to Open (Read Me).txt"
Remon AI Background Remover Pro V 01.02
===================================================

EASIEST WAY TO INSTALL & OPEN (RECOMMENDED):
---------------------------------------------------
1. Double-click "1-Click Install & Launch.command" inside this folder.
   It will automatically install to /Applications, bypass macOS Gatekeeper
   ("damaged / cannot be opened" error), and launch the app immediately!

MANUAL DRAG & DROP METHOD:
---------------------------------------------------
1. Drag "Remon AI Background Remover Pro V 01.02" into the "Applications" shortcut.
2. If macOS shows: "cannot be opened because Apple cannot check it for malicious software"
   or "is damaged and can't be opened":
   -> Right-Click (or Control-Click) the app in Applications and choose "Open", then click "Open".
   OR
   -> Open System Settings > Privacy & Security, scroll down and click "Open Anyway".
   OR
   -> Run this one-line command in Terminal:
      xattr -cr "/Applications/Remon AI Background Remover Pro V 01.02.app"

FEATURES:
- 100% Offline AI background removal (BRIA RMBG 2.0 ONNX model pre-bundled).
- Zero setup or Python install required.
- Instant opening with lazy-loaded AI engine.
EOF

echo "6. Stripping extended attributes from staging..."
xattr -cr "${STAGING_DIR}" || true

echo "7. Generating compressed .dmg disk image with hdiutil (HFS+)..."
hdiutil create -volname "Remon AI Background Remover Pro" \
               -srcfolder "${STAGING_DIR}" \
               -fs HFS+ \
               -ov -format UDZO \
               "${DMG_PATH}"

echo "8. Cleaning up staging directory..."
rm -rf "${STAGING_DIR}"

echo "=== SUCCESS! DMG created at: ${DMG_PATH} ==="
ls -lh "${DMG_PATH}"
