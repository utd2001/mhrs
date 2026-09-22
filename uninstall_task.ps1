$task = Get-ScheduledTask -TaskName "MHRS Randevu Kontrolu" -ErrorAction SilentlyContinue

if ($task) {
    Unregister-ScheduledTask -TaskName "MHRS Randevu Kontrolu" -Confirm:$false
    Write-Host "Gorev kaldirildi: MHRS Randevu Kontrolu."
} else {
    Write-Host "MHRS Randevu Kontrolu adinda kayitli bir gorev bulunamadi."
}
