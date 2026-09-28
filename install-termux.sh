#!/data/data/com.termux/files/usr/bin/bash
#
# MADRATIF - installer untuk HP (Termux, sisi master/controller).
#
# Satu baris (ganti KODE dengan kode rahasiamu, sama dengan yang di PC):
#   curl -s https://raw.githubusercontent.com/matif-dev/madratif/main/install-termux.sh | bash -s -- KODE
#
set -e

CODE="$1"

echo "=== MADRATIF (Termux master) ==="
pkg install -y python git
pip install --upgrade "git+https://github.com/matif-dev/madratif"

if [ -z "$CODE" ]; then
    printf "Masukkan kode rahasia (sama dengan di PC): "
    read CODE
fi

madratif connect "$CODE"

echo ""
echo "Siap! Langsung coba:"
echo "  madratif clients"
