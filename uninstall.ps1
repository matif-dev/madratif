<#
  MADRATIF - uninstaller untuk PC Windows.
  Jalankan:
    powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
  Tambah -Purge untuk sekalian menghapus konfigurasi (~/.madratif).
#>
[CmdletBinding()]
param([switch]$Purge)

Write-Host "=== MADRATIF uninstall ===" -ForegroundColor Cyan
$ErrorActionPreference = "SilentlyContinue"

# hentikan agent yang sedang jalan
Get-CimInstance Win32_Process -Filter "Name like '%python%'" |
    Where-Object { $_.CommandLine -like "*madratif*client*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

# hapus autostart
$startup = [Environment]::GetFolderPath("Startup")
Remove-Item (Join-Path $startup "MADRATIF.lnk") -Force
$cfgDir = Join-Path $env:USERPROFILE ".madratif"
Remove-Item (Join-Path $cfgDir "madratif-autostart.vbs") -Force

# pilih python
$py = "python"
try { $null = & $py --version 2>&1; if ($LASTEXITCODE -ne 0) { $py = "py" } } catch { $py = "py" }

# uninstall paket
& $py -m pip uninstall -y madratif

if ($Purge) {
    Remove-Item -Recurse -Force $cfgDir
    Write-Host "Konfigurasi dihapus." -ForegroundColor Yellow
}

Write-Host "MADRATIF sudah dihapus." -ForegroundColor Green
