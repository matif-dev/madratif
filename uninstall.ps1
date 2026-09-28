<#
  MADRATIF - uninstaller ALL-IN-ONE. Jalankan satu baris:

    irm https://raw.githubusercontent.com/matif-dev/madratif/main/uninstall.ps1 | iex

  Untuk sekalian hapus konfigurasi (network key), set dulu:
    $env:MADRATIF_PURGE = "1"
#>

$ErrorActionPreference = 'SilentlyContinue'
Write-Host "=== MADRATIF uninstall ===" -ForegroundColor Cyan

# 1. hentikan agent yang sedang jalan
Get-CimInstance Win32_Process -Filter "Name like '%python%'" |
    Where-Object { $_.CommandLine -like '*madratif*client*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

# 2. hapus autostart
$startup = [Environment]::GetFolderPath('Startup')
Remove-Item (Join-Path $startup 'MADRATIF.lnk') -Force

# 3. hapus folder aplikasi
$base = Join-Path $env:LOCALAPPDATA 'madratif'
Remove-Item $base -Recurse -Force

# 4. konfigurasi
$cfgDir = Join-Path $env:USERPROFILE '.madratif'
if ($env:MADRATIF_PURGE) {
    Remove-Item $cfgDir -Recurse -Force
    Write-Host "Konfigurasi (network key) ikut dihapus." -ForegroundColor Yellow
} else {
    Write-Host "Konfigurasi disimpan di $cfgDir (set MADRATIF_PURGE=1 untuk hapus juga)." -ForegroundColor DarkGray
}

Write-Host "MADRATIF sudah dihapus dari PC ini." -ForegroundColor Green
