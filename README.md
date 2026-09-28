# MADRATIF

Kontrol beberapa PC Windows **milikmu sendiri** dari HP (Termux) atau terminal
mana pun, lewat sebuah broker MQTT. Kamu buka terminal di PC, install, lalu PC
itu menunggu perintah. Dari HP kamu ketik perintah dengan prefix `madratif`.

> **Untuk penggunaan pribadi.** Install hanya di komputer milik sendiri.
> Perintah yang tersedia sengaja dibatasi (buka Chrome, screensaver, status,
> ping) - **tidak ada eksekusi perintah/shell sembarangan**. Ini alat kendali
> pribadi, bukan alat peretasan.

## Fitur (versi sekarang)

| Perintah | Aksi di PC target |
|---|---|
| `madratif clients` | daftar semua client yang online |
| `madratif google <url> <client>` | buka Chrome ke `<url>` |
| `madratif screensaver <client>` | buka jendela screensaver teks besar "MADRATIF" yang memantul & beranimasi |
| `madratif status <client>` | buka jendela panel status client (hostname, IP, dsb.) |
| `madratif ping <client>` | cek client masih hidup |

Pakai `all` sebagai `<client>` untuk mengirim ke semua PC sekaligus.

## Cara kerja singkat

```
   HP (Termux)                 Broker MQTT                 PC Windows
  "madratif ..."   ───pub──▶   broker.emqx.io   ───sub──▶   madratif agent
      controller               (network key)                 client
```

- **Broker MQTT** menghubungkan HP dan PC tanpa perlu port-forwarding, bahkan
  beda jaringan/internet. Default memakai broker publik gratis `broker.emqx.io`.
- **Network key** adalah kata sandi acak yang mengisolasi device kamu di broker.
  Semua device kamu harus memakai network key yang **sama**.

## Install di PC (Windows) - sisi client

Buka **PowerShell** di PC yang mau dikontrol, lalu (dari folder repo yang sudah
di-clone / di-download):

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -ClientId client-1
```

Atau langsung dari GitHub (ganti `matif-dev`):

```powershell
irm https://raw.githubusercontent.com/matif-dev/madratif/main/install.ps1 | iex
```

Installer akan: memastikan Python ada, meng-install paket, membuat network key
(kalau belum ada), dan menyimpan konfigurasi. Catat **network key** yang muncul.

Jalankan client (menunggu perintah):

```powershell
python -m madratif client start
```

Ingin otomatis jalan saat login? Tambahkan `-Autostart` saat install:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -ClientId client-1 -Autostart
```

Punya beberapa PC? Install di tiap PC dengan **network key yang sama** tapi
`-ClientId` berbeda (`client-1`, `client-2`, ...):

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -NetworkKey <KEY-SAMA> -ClientId client-2
```

## Install di HP (Termux) - sisi controller

Di Termux:

```bash
pkg install -y python git
pip install "git+https://github.com/matif-dev/madratif"
madratif setup     # isi network key yang SAMA dengan PC
```

atau pakai skrip:

```bash
bash install-termux.sh https://github.com/matif-dev/madratif
```

## Pakai

```bash
madratif clients
madratif google https://roblox.com client-1
madratif screensaver client-1
madratif status client-1
madratif ping client-1

# broadcast ke semua PC:
madratif screensaver all
```

## Uninstall

Di PC (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
# hapus sekalian konfigurasinya:
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1 -Purge
```

Di Termux:

```bash
pip uninstall -y madratif
```

## Konfigurasi

Tersimpan di `~/.madratif/config.json`:

```json
{
  "broker": "broker.emqx.io",
  "port": 1883,
  "network_key": "xxxxxxxx",
  "client_id": "client-1",
  "username": "",
  "password": "",
  "tls": false
}
```

Ubah kapan saja dengan `madratif setup`, atau lewat environment variable
(`MADRATIF_BROKER`, `MADRATIF_KEY`, `MADRATIF_CLIENT_ID`, dst).

## Catatan keamanan & privasi

- Broker publik `broker.emqx.io` **tidak terenkripsi** dan dipakai bersama.
  Network key acak membuat topik kamu sulit ditebak, tapi ini **bukan** jaminan
  keamanan kuat. Untuk privasi lebih baik, pakai broker MQTT sendiri dengan
  username/password + TLS (isi `username`, `password`, `tls: true`, `port: 8883`).
- Kumpulan aksi sengaja dibatasi dan tetap (allowlist). Tidak ada fitur untuk
  menjalankan perintah sembarang, mengambil file, atau menyembunyikan diri.

## Menambah fitur nanti

Aksi baru cukup ditambahkan di dua tempat:
`src/madratif/actions.py` (implementasi) dan `_handle()` di
`src/madratif/agent.py` (routing), lalu perintahnya di `src/madratif/cli.py`.

## Lisensi

MIT - lihat [LICENSE](LICENSE).
