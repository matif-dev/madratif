<#
  MADRATIF - installer ALL-IN-ONE untuk client Windows.

  Cukup jalankan SATU baris ini di PowerShell (Windows baru pun bisa):

    irm https://raw.githubusercontent.com/matif-dev/madratif/main/install.ps1 | iex

  - Tidak perlu install Python duluan: kalau belum ada, otomatis diunduh
    versi portable (tanpa admin).
  - Tidak perlu pip: aplikasinya murni standard library.
  - Otomatis dikonfigurasi, dipasang autostart, dan langsung dijalankan.

  Opsi lewat environment variable (opsional, untuk tanpa tanya-jawab):
    $env:MADRATIF_KEY        = "kunci-sama-untuk-semua-device"
    $env:MADRATIF_CLIENT_ID  = "client-1"
    $env:MADRATIF_NOAUTOSTART = "1"   # jangan pasang autostart
    $env:MADRATIF_NOSTART     = "1"   # jangan langsung jalankan
#>

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

Write-Host ""
Write-Host "=== MADRATIF - install all-in-one (client) ===" -ForegroundColor Cyan

$base = Join-Path $env:LOCALAPPDATA 'madratif'
$lib = Join-Path $base 'lib'
New-Item -ItemType Directory -Force -Path $base | Out-Null

# --- 1. Python: pakai yang ada, kalau tidak ada unduh portable -------------
function Get-WorkingPython {
    foreach ($c in @('python', 'py')) {
        try {
            $exe = (& $c -c "import sys;print(sys.executable)" 2>$null)
            if ($LASTEXITCODE -eq 0 -and $exe) { return $exe.Trim() }
        } catch {}
    }
    return $null
}

$pyExe = Get-WorkingPython
$embeddable = $false
if (-not $pyExe) {
    Write-Host "Python belum ada - mengunduh Python portable (sekali saja)..." -ForegroundColor Yellow
    $emb = Join-Path $base 'python'
    $pyExe = Join-Path $emb 'python.exe'
    if (-not (Test-Path $pyExe)) {
        $zip = Join-Path $base 'python-portable.zip'
        Invoke-WebRequest 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile $zip -UseBasicParsing
        New-Item -ItemType Directory -Force -Path $emb | Out-Null
        Expand-Archive $zip -DestinationPath $emb -Force
        Remove-Item $zip -Force
    }
    $embeddable = $true
}
Write-Host "Python: $pyExe" -ForegroundColor Green

# --- 2. Unduh kode MADRATIF (tanpa dependency, tanpa pip) ------------------
Write-Host "Mengunduh MADRATIF..." -ForegroundColor Cyan
$srcZip = Join-Path $base 'madratif-src.zip'
Invoke-WebRequest 'https://github.com/matif-dev/madratif/archive/refs/heads/main.zip' -OutFile $srcZip -UseBasicParsing
$ext = Join-Path $base 'extract'
if (Test-Path $ext) { Remove-Item $ext -Recurse -Force }
Expand-Archive $srcZip -DestinationPath $ext -Force
Remove-Item $srcZip -Force
$srcPkg = Join-Path $ext 'madratif-main\src\madratif'

if ($embeddable) {
    $pkgDest = Join-Path (Split-Path $pyExe -Parent) 'madratif'
    $pyPathForRun = ''
} else {
    New-Item -ItemType Directory -Force -Path $lib | Out-Null
    $pkgDest = Join-Path $lib 'madratif'
    $pyPathForRun = $lib
}
if (Test-Path $pkgDest) { Remove-Item $pkgDest -Recurse -Force }
Copy-Item $srcPkg $pkgDest -Recurse -Force
Remove-Item $ext -Recurse -Force
Write-Host "Kode terpasang." -ForegroundColor Green

# --- 3. Konfigurasi -------------------------------------------------------
$key = $env:MADRATIF_KEY
if (-not $key -and [Environment]::UserInteractive) {
    $key = Read-Host "Network key (Enter = buat baru; harus SAMA di semua device)"
}
if (-not $key) {
    $key = [guid]::NewGuid().ToString('n').Substring(0, 16)
    Write-Host "Network key baru dibuat otomatis." -ForegroundColor Yellow
}

# Nama client otomatis dari nama komputer (tidak perlu diisi / dicatat).
$cid = $env:MADRATIF_CLIENT_ID
if (-not $cid) { $cid = $env:COMPUTERNAME.ToLower() }

$cfgDir = Join-Path $env:USERPROFILE '.madratif'
New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
$cfg = [ordered]@{
    broker = 'broker.emqx.io'; port = 1883; network_key = $key;
    client_id = $cid; username = ''; password = ''; tls = $false
}
($cfg | ConvertTo-Json) | Out-File (Join-Path $cfgDir 'config.json') -Encoding utf8

# --- 4. Launcher (shim) ---------------------------------------------------
$pythonw = $pyExe -replace 'python\.exe$', 'pythonw.exe'
if (-not (Test-Path $pythonw)) { $pythonw = $pyExe }

$agentCmd = Join-Path $base 'agent.cmd'
@"
@echo off
set "PYTHONPATH=$pyPathForRun"
"$pythonw" -m madratif client start
"@ | Out-File $agentCmd -Encoding ascii

$madratifCmd = Join-Path $base 'madratif.cmd'
@"
@echo off
set "PYTHONPATH=$pyPathForRun"
"$pyExe" -m madratif %*
"@ | Out-File $madratifCmd -Encoding ascii

# --- 5. Autostart ---------------------------------------------------------
if (-not $env:MADRATIF_NOAUTOSTART) {
    $startup = [Environment]::GetFolderPath('Startup')
    $vbs = Join-Path $base 'autostart.vbs'
    @"
Set s = CreateObject("Wscript.Shell")
s.Run "cmd /c " & Chr(34) & "$agentCmd" & Chr(34), 0, False
"@ | Out-File $vbs -Encoding ascii
    $lnk = Join-Path $startup 'MADRATIF.lnk'
    $ws = New-Object -ComObject WScript.Shell
    $sc = $ws.CreateShortcut($lnk)
    $sc.TargetPath = 'wscript.exe'
    $sc.Arguments = """$vbs"""
    $sc.Save()
    Write-Host "Autostart aktif (jalan otomatis & tersembunyi saat login)." -ForegroundColor Green
}

# --- 6. Ringkasan + jalankan ----------------------------------------------
Write-Host ""
Write-Host "SELESAI." -ForegroundColor Cyan
Write-Host "  Network key : $key" -ForegroundColor Yellow
Write-Host "  Client ID   : $cid"
Write-Host "  Broker      : broker.emqx.io:1883"
Write-Host ""
Write-Host "Pakai KODE ini juga di HP (Termux). Tidak perlu dicatat kalau kamu yang menentukannya." -ForegroundColor Yellow
Write-Host ""

if ($env:MADRATIF_NOSTART) {
    Write-Host "Jalankan client kapan saja lewat:  $agentCmd"
} else {
    $env:PYTHONPATH = $pyPathForRun
    Start-Process -FilePath $pythonw -ArgumentList @('-m', 'madratif', 'client', 'start') -WindowStyle Hidden
    Write-Host "Client sudah jalan DI BACKGROUND. Terminal ini boleh langsung ditutup." -ForegroundColor Green
}
