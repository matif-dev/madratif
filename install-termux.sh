#!/data/data/com.termux/files/usr/bin/bash
#
# MADRATIF - installer untuk HP (Termux, sisi controller).
# Pakai:
#   bash install-termux.sh
#   # atau dengan URL repo kamu:
#   bash install-termux.sh https://github.com/matif-dev/madratif
#
set -e

echo "=== MADRATIF (Termux controller) ==="
pkg update -y || true
pkg install -y python git

DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="${1:-https://github.com/matif-dev/madratif}"

if [ -f "$DIR/pyproject.toml" ]; then
    echo "Menginstall dari folder lokal..."
    pip install --upgrade "$DIR"
else
    echo "Menginstall dari GitHub: $REPO"
    pip install --upgrade "git+$REPO"
fi

echo ""
echo "Terinstall. Sekarang konfigurasi (samakan NETWORK KEY dengan PC kamu):"
madratif setup

echo ""
echo "Selesai. Coba jalankan:"
echo "  madratif clients"
