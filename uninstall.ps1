$task = Get-ScheduledTask -TaskName "MHRS Randevu Kontrolu" -ErrorAction SilentlyContinue

if ($task) {
    Unregister-ScheduledTask -TaskName "MHRS Randevu Kontrolu" -Confirm:$false
    Write-Host "Gorev kaldirildi: MHRS Randevu Kontrolu."
} else {
    Write-Host "MHRS Randevu Kontrolu adinda kayitli bir gorev bulunamadi."
}

if (Test-Path "$PSScriptRoot\chrome_profile") {
    Remove-Item "$PSScriptRoot\chrome_profile" -Recurse -Force
    Write-Host "chrome_profile klasoru silindi."
}

if (Test-Path "$PSScriptRoot\config.local.ps1") {
    Remove-Item "$PSScriptRoot\config.local.ps1" -Force
    Write-Host "config.local.ps1 silindi."
}

if (-not (Test-Path "$PSScriptRoot\config.local.example.ps1")) {
    $Iu = [char]0x0130   # İ
    $gb = [char]0x011F   # ğ
    $content = "`$Il = `"${Iu}STANBUL`"`r`n`$Klinik = `"Aile Hekimli${gb}i`"`r`n`$Hastane = `"Fatih Sultan Mehmet`"`r`n"
    [System.IO.File]::WriteAllText("$PSScriptRoot\config.local.example.ps1", $content, [System.Text.UTF8Encoding]::new($true))
    Write-Host "config.local.example.ps1 geri getirildi."
}
