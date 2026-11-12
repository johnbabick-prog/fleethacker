#!/bin/sh
# Run this on your Mac to produce a ready-to-send zip for Windows.
# Usage:  ./deploy/windows/build-windows-package.sh
set -eu
cd "$(dirname "$0")/../.."

echo "Building Docker image for linux/amd64..."
docker build --platform linux/amd64 -t fleethacker:latest .

echo "Exporting image to tar..."
docker save fleethacker:latest -o deploy/windows/fleethacker-image.tar

# Create api_key.txt placeholder if it doesn't exist
if [ ! -f deploy/windows/api_key.txt ]; then
    echo "PASTE_YOUR_EDGERUNNER_API_KEY_HERE" > deploy/windows/api_key.txt
fi

echo "Creating zip package..."
cd deploy/windows
zip -j FleetTech-Windows.zip \
    setup.bat \
    setup.ps1 \
    "Fleet Tech.bat" \
    run.ps1 \
    api_key.txt \
    fleethacker-image.tar

SIZE=$(du -h FleetTech-Windows.zip | cut -f1)
echo ""
echo "Done!  deploy/windows/FleetTech-Windows.zip ($SIZE)"
echo ""
echo "Send that zip to the Windows user. Instructions:"
echo "  1. Unzip"
echo "  2. Edit api_key.txt — paste the EdgeRunner API key"
echo "  3. Double-click setup.bat  (one-time, needs admin)"
echo "  4. Double-click 'Fleet Tech.bat' to launch"
