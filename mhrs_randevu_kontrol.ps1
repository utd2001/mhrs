chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PYTHONLEGACYWINDOWSSTDIO = "0"

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "HATA: 'python' PATH icinde bulunamadi. Python kurulu oldugundan ve PATH'e eklendiginden emin olun."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}
$pythonExe = $pythonCmd.Source
$script = Join-Path $PSScriptRoot "mhrs_randevu_ara.py"

# Gercek arama parametreleri config.local.ps1 icinde tutulur (repoya dahil edilmez).
# Yoksa asagidaki genel ornek degerler kullanilir.
$Il = "İSTANBUL"
$Klinik = "Aile Hekimliği"
$Hastane = "Fatih Sultan Mehmet"

$configPath = Join-Path $PSScriptRoot "config.local.ps1"
if (Test-Path $configPath) {
    . $configPath
}

$argList = @(
    $script,
    "--il", $Il,
    "--klinik", $Klinik,
    "--hastane", $Hastane
)

& $pythonExe @argList

Write-Host ""
Write-Host "Devam etmek icin bir tusa basin..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
