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

## Satu KODE untuk semuanya

Tentukan **satu kode rahasia** milikmu (bebas, mis. `naga-merah-77`). Kode itu:
- menghubungkan semua device kamu, dan
- jadi kunci akses - hanya yang tahu kodenya yang bisa menyambung.

Pakai kode yang **sama** di PC dan di HP. Karena kamu yang menentukan, tidak ada
yang perlu dicatat dari layar.

## Install di PC (Windows) - sisi client (ALL-IN-ONE)

Buka **PowerShell**, tempel **satu baris** ini (ganti `KODE` dengan kodemu).
Windows baru pun langsung bisa - tidak perlu install Python/pip dulu:

```powershell
$env:MADRATIF_KEY="KODE"; irm https://raw.githubusercontent.com/matif-dev/madratif/main/install.ps1 | iex
```

Selesai. Otomatis: unduh Python portable kalau belum ada, pasang aplikasi,
konfigurasi, **autostart**, lalu jalankan agent **di background**. Tidak ada
pertanyaan, tidak ada yang perlu dicatat - **terminal boleh langsung ditutup**.

Punya beberapa PC? Tempel baris yang sama (kode sama) di tiap PC. Nama client
otomatis dari nama komputer, jadi tiap PC beda sendiri.

## Install di HP (Termux) - sisi master

Tempel **satu baris** ini di Termux (ganti `KODE` dengan kode yang sama):

```bash
curl -s https://raw.githubusercontent.com/matif-dev/madratif/main/install-termux.sh | bash -s -- KODE
```

Selesai - langsung tersambung, tanpa isi-isi lagi. Habis itu tinggal perintah:

```bash
madratif clients
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

### Prank (buat PC sendiri / teman yang izin)

```bash
madratif say halo aku mengawasimu client-1   # PC ngomong (TTS)
madratif notify ada hantu di belakangmu client-1
madratif rickroll client-1                   # Rick Astley fullscreen
madratif beep client-1
madratif wallpaper https://.../lucu.jpg client-1
madratif wallpaper reset client-1            # balikin wallpaper
madratif matrix client-1                     # hujan kode hijau
madratif fakeupdate client-1                 # "Windows Update" palsu
madratif minimize client-1                   # minimize semua jendela
madratif volume max client-1                 # atau: volume 30
madratif spin client-1                       # putar layar 180
madratif unspin client-1                     # balikin normal
madratif bsod client-1                       # blue screen palsu
madratif disco client-1                      # layar kedip warna
madratif countdown 10 client-1               # hitung mundur "self-destruct"
```

Semua reversible: layar prank ditutup dengan menekan tombol apa saja,
`unspin` membalik layar, `wallpaper reset` mengembalikan wallpaper.

## Update otomatis

Setiap client **mengecek repo GitHub secara berkala** (default tiap ~10 menit).
Kalau ada commit baru di `main`, client menarik kode terbaru lalu **restart
sendiri** - jadi kamu cukup:

1. Edit/ tambah command di kode,
2. `git push`,
3. semua PC ikut ter-update otomatis (tanpa install ulang).

Mau langsung tanpa nunggu? Paksa dari master:

```bash
madratif update nama-pc     # satu PC
madratif update all         # semua PC
```

Catatan: update menarik & menjalankan kode dari repomu sendiri. Jaga akun GitHub
kamu. Matikan lewat config: `auto_update: false` atau `update_interval: 0`.

### Menambah command baru

1. `actions.py` - tulis fungsi aksinya.
2. `agent.py` - daftarkan di `_handle()`.
3. `cli.py` - tambah perintah controller-nya.
4. `git push` -> client update sendiri.

## Uninstall

Di PC (PowerShell), satu baris:

```powershell
irm https://raw.githubusercontent.com/matif-dev/madratif/main/uninstall.ps1 | iex
```

Untuk sekalian hapus konfigurasi (network key):

```powershell
$env:MADRATIF_PURGE="1"; irm https://raw.githubusercontent.com/matif-dev/madratif/main/uninstall.ps1 | iex
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
- **Tanpa dependency pihak ketiga**: aplikasi ini murni standard library Python
  (punya klien MQTT mini sendiri di `mqtt_mini.py`), jadi bisa jalan di Python
  portable tanpa pip.

## Menambah fitur nanti

Aksi baru cukup ditambahkan di dua tempat:
`src/madratif/actions.py` (implementasi) dan `_handle()` di
`src/madratif/agent.py` (routing), lalu perintahnya di `src/madratif/cli.py`.

## Lisensi

MIT - lihat [LICENSE](LICENSE).
