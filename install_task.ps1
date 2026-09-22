$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\mhrs_randevu_kontrol.ps1`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 3650)

Register-ScheduledTask -TaskName "MHRS Randevu Kontrolu" -Action $action -Trigger $trigger -Force

Write-Host "Gorev kuruldu: MHRS Randevu Kontrolu (her saat basi calisir)."
