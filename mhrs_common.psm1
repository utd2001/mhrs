# MHRS ortak PowerShell fonksiyonlari.
# install.ps1, uninstall.ps1 ve mhrs_randevu_kontrol.ps1 tarafindan
# `Import-Module "$PSScriptRoot\mhrs_common.psm1"` ile kullanilir.

$script:TaskName = "MHRS Randevu Kontrolu"

function Set-MhrsUtf8Console {
    <# Konsolu UTF-8'e ayarlar (Turkce karakterler icin gerekli). #>
    chcp 65001 > $null
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONUTF8 = "1"
    $env:PYTHONLEGACYWINDOWSSTDIO = "0"
}

function Get-MhrsPythonExe {
    <# PATH'teki python.exe yolunu dondurur; bulunamazsa $null. #>
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        return $null
    }
    return $pythonCmd.Source
}

function Invoke-MhrsScript {
    <# mhrs.py'yi calistirir; python bulunamazsa hata basar. #>
    param([string]$RootPath)

    $pythonExe = Get-MhrsPythonExe
    if (-not $pythonExe) {
        Write-Host "HATA: 'python' PATH icinde bulunamadi. Python kurulu oldugundan ve PATH'e eklendiginden emin olun."
        return $false
    }

    $script = Join-Path $RootPath "mhrs.py"
    & $pythonExe $script
    return $true
}

function Install-MhrsTask {
    <# config.local.ps1 varsa saatlik Gorev Zamanlayici gorevini kurar. #>
    param([string]$RootPath)

    if (-not (Test-Path (Join-Path $RootPath "config.local.ps1"))) {
        Write-Host "config.local.ps1 henuz yok. Once 'python -X utf8 mhrs.py' calistirip"
        Write-Host "Il/Klinik/Hastane secimlerinizi kaydedin, ardindan bu kurulumu tekrar calistirin."
        return $false
    }

    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RootPath\mhrs_randevu_kontrol.ps1`""
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
        -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 3650)

    Register-ScheduledTask -TaskName $script:TaskName -Action $action -Trigger $trigger -Force | Out-Null
    Write-Host "Gorev kuruldu: $script:TaskName (her saat basi calisir)."
    return $true
}

function Uninstall-MhrsTask {
    <# Kurulu Gorev Zamanlayici gorevini kaldirir. #>
    $task = Get-ScheduledTask -TaskName $script:TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $script:TaskName -Confirm:$false
        Write-Host "Gorev kaldirildi: $script:TaskName."
    } else {
        Write-Host "$script:TaskName adinda kayitli bir gorev bulunamadi."
    }
}

function Remove-MhrsLocalData {
    <# chrome_profile/ ve config.local.ps1 dosyalarini siler. #>
    param([string]$RootPath)

    $profilePath = Join-Path $RootPath "chrome_profile"
    if (Test-Path $profilePath) {
        Remove-Item $profilePath -Recurse -Force
        Write-Host "chrome_profile klasoru silindi."
    }

    $configPath = Join-Path $RootPath "config.local.ps1"
    if (Test-Path $configPath) {
        Remove-Item $configPath -Force
        Write-Host "config.local.ps1 silindi."
    }
}

function Restore-MhrsExampleConfig {
    <# config.local.example.ps1 yoksa varsayilan icerikle yeniden olusturur. #>
    param([string]$RootPath)

    $examplePath = Join-Path $RootPath "config.local.example.ps1"
    if (Test-Path $examplePath) {
        return
    }

    $Iu = [char]0x0130   # İ
    $gb = [char]0x011F   # ğ
    $content = "`$Il = `"${Iu}STANBUL`"`r`n`$Klinik = `"Aile Hekimli${gb}i`"`r`n`$Hastane = `"Fatih Sultan Mehmet`"`r`n"
    [System.IO.File]::WriteAllText($examplePath, $content, [System.Text.UTF8Encoding]::new($true))
    Write-Host "config.local.example.ps1 geri getirildi."
}

Export-ModuleMember -Function `
    Set-MhrsUtf8Console, `
    Get-MhrsPythonExe, `
    Invoke-MhrsScript, `
    Install-MhrsTask, `
    Uninstall-MhrsTask, `
    Remove-MhrsLocalData, `
    Restore-MhrsExampleConfig
