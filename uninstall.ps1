Import-Module "$PSScriptRoot\mhrs_common.psm1" -Force

Uninstall-MhrsTask
Remove-MhrsLocalData -RootPath $PSScriptRoot
Restore-MhrsExampleConfig -RootPath $PSScriptRoot
