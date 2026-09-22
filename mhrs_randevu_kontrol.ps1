Import-Module "$PSScriptRoot\mhrs_common.psm1" -Force

Set-MhrsUtf8Console

$ok = Invoke-MhrsScript -RootPath $PSScriptRoot
if (-not $ok) {
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host ""
Write-Host "Devam etmek icin bir tusa basin..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
