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
# --force-reinstall --no-cache-dir supaya SELALU dapat versi terbaru dari repo
# (kalau tidak, pip bisa melewati update karena nomor versi kebetulan sama).
pip install --upgrade --force-reinstall --no-cache-dir "git+https://github.com/matif-dev/madratif"

if [ -z "$CODE" ]; then
    printf "Masukkan kode rahasia (sama dengan di PC): "
    read CODE
fi

madratif connect "$CODE"

echo ""
echo "Siap! Langsung coba:"
echo "  madratif clients"
