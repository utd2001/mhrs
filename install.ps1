Import-Module "$PSScriptRoot\mhrs_common.psm1" -Force

$ok = Install-MhrsTask -RootPath $PSScriptRoot
if (-not $ok) {
    exit 1
}
