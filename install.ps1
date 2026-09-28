<#
  MADRATIF - installer untuk PC Windows (client).
  Jalankan di PowerShell:

    # dari folder repo yang sudah di-clone:
    powershell -ExecutionPolicy Bypass -File .\install.ps1

    # atau langsung dari internet (ganti URL repo kamu):
    irm https://raw.githubusercontent.com/matif-dev/madratif/main/install.ps1 | iex

  Parameter opsional:
    -NetworkKey  <key>    samakan dengan device lain (kosong = dibuat acak)
    -ClientId    <nama>   nama client, mis. client-1  (default: nama komputer)
    -Broker      <host>   default broker.emqx.io
    -Port        <int>    default 1883
    -Autostart            jalankan client otomatis saat login
    -RepoUrl     <url>    URL repo GitHub kamu
#>
[CmdletBinding()]
param(
    [string]$NetworkKey = "",
    [string]$ClientId = "",
    [string]$Broker = "broker.emqx.io",
    [int]$Port = 1883,
    [switch]$Autostart,
    [string]$RepoUrl = "https://github.com/matif-dev/madratif"
)

$ErrorActionPreference = "Stop"
Write-Host "=== MADRATIF installer ===" -ForegroundColor Cyan

function Get-Python {
    foreach ($c in @("python", "py")) {
        try {
            $null = & $c --version 2>&1
            if ($LASTEXITCODE -eq 0) { return $c }
        } catch {}
    }
    return $null
}

$py = Get-Python
if (-not $py) {
    Write-Host "Python tidak ditemukan. Mencoba install lewat winget..." -ForegroundColor Yellow
    try {
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    } catch {
        Write-Host "Gagal auto-install. Install Python dari https://www.python.org/downloads/ (centang 'Add to PATH'), lalu jalankan ulang." -ForegroundColor Red
        exit 1
    }
    $py = Get-Python
    if (-not $py) {
        Write-Host "Python masih belum terdeteksi. Tutup lalu buka terminal baru dan ulangi." -ForegroundColor Red
        exit 1
    }
}
Write-Host "Python: $(& $py --version)" -ForegroundColor Green

# --- install paket ---
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$localPkg = Join-Path $scriptDir "pyproject.toml"
if (Test-Path $localPkg) {
    Write-Host "Menginstall dari folder lokal..." -ForegroundColor Cyan
    & $py -m pip install --user --upgrade "$scriptDir"
} else {
    Write-Host "Menginstall dari GitHub: $RepoUrl" -ForegroundColor Cyan
    & $py -m pip install --user --upgrade "git+$RepoUrl"
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install gagal." -ForegroundColor Red
    exit 1
}

# --- konfigurasi ---
if (-not $ClientId) { $ClientId = ($env:COMPUTERNAME).ToLower() }
if (-not $NetworkKey) {
    $NetworkKey = (& $py -c "import secrets;print(secrets.token_urlsafe(9))").Trim()
    Write-Host "Network key dibuat otomatis: $NetworkKey" -ForegroundColor Yellow
}

$cfgDir = Join-Path $env:USERPROFILE ".madratif"
New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
$cfg = [ordered]@{
    broker      = $Broker
    port        = $Port
    network_key = $NetworkKey
    client_id   = $ClientId
    username    = ""
    password    = ""
    tls         = $false
}
($cfg | ConvertTo-Json) | Out-File -FilePath (Join-Path $cfgDir "config.json") -Encoding utf8
Write-Host "Config disimpan: $cfgDir\config.json" -ForegroundColor Green

# --- autostart opsional ---
if ($Autostart) {
    $startup = [Environment]::GetFolderPath("Startup")
    $vbs = Join-Path $cfgDir "madratif-autostart.vbs"
    $pythonw = (& $py -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))").Trim()
    if (-not (Test-Path $pythonw)) { $pythonw = "pythonw" }
    @"
Set s = CreateObject("Wscript.Shell")
s.Run "$pythonw -m madratif client start", 0, False
"@ | Out-File -FilePath $vbs -Encoding ascii
    $lnk = Join-Path $startup "MADRATIF.lnk"
    $ws = New-Object -ComObject WScript.Shell
    $sc = $ws.CreateShortcut($lnk)
    $sc.TargetPath = "wscript.exe"
    $sc.Arguments = "`"$vbs`""
    $sc.Save()
    Write-Host "Autostart aktif (folder Startup). Client jalan otomatis saat login." -ForegroundColor Green
}

Write-Host ""
Write-Host "SELESAI." -ForegroundColor Cyan
Write-Host "  Network key : $NetworkKey"
Write-Host "  Client ID   : $ClientId"
Write-Host "  Broker      : $Broker`:$Port"
Write-Host ""
Write-Host "Jalankan client sekarang (menunggu perintah dari HP):" -ForegroundColor Yellow
Write-Host "  $py -m madratif client start"
Write-Host ""
Write-Host "Di HP (Termux), pakai NETWORK KEY yang sama: $NetworkKey" -ForegroundColor Yellow
