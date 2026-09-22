@echo off
chcp 65001 > nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo HATA: 'python' PATH icinde bulunamadi. Python kurulu oldugundan ve PATH'e eklendiginden emin olun.
    pause
    exit /b 1
)

python -X utf8 mhrs.py

echo.
echo Devam etmek icin bir tusa basin...
pause >nul
