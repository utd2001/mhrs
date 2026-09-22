"""
MHRS Randevu Otomasyonu - ana giris noktasi.

Kullanim:
    python -X utf8 mhrs.py [--show]

Akis:
    1. Oturum acik degilse (chrome_profile/ yoksa) e-Devlet ile giris
       yaptirir (mhrs_login.py).
    2. config.local.ps1 yoksa Randevu Ara formunu tarayicida acar; Il,
       Klinik, Hastane alanlarini kullanici elle secer ve secimler
       config.local.ps1'e kaydedilir (mhrs_ayar_kaydet.py).
    3. config.local.ps1'deki Il/Klinik/Hastane degerleriyle randevu
       aramasini calistirir ve sonucu msgbox ile bildirir
       (mhrs_randevu_ara.py).

Turkce karakterlerin (İ, Ö, Ş, Ç, Ğ, Ü) dogru okunmasi icin "-X utf8"
bayragiyla calistirmak onerilir.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from mhrs_ayar_kaydet import PROFILE_DIR, ensure_logged_in, run_ayar_kaydet
from mhrs_randevu_ara import run_randevu_ara

CONFIG_PATH = Path(__file__).resolve().parent / "config.local.ps1"

_PS1_VAR_RE = re.compile(r'^\$(\w+)\s*=\s*"(.*)"\s*$')


def read_config() -> dict[str, str]:
    """config.local.ps1 icindeki $Il/$Klinik/$Hastane atamalarini okur."""
    values: dict[str, str] = {}
    for line in CONFIG_PATH.read_text(encoding="utf-8-sig").splitlines():
        match = _PS1_VAR_RE.match(line.strip())
        if match:
            values[match.group(1)] = match.group(2)
    return values


def ensure_login() -> None:
    if PROFILE_DIR.exists():
        return
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    try:
        ensure_logged_in(driver)
    finally:
        driver.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="MHRS randevu otomasyonu")
    parser.add_argument("--show", action="store_true", help="Randevu aramasini gorunur tarayicida calistir")
    args = parser.parse_args()

    ensure_login()

    if not CONFIG_PATH.exists():
        print("Arama ayarlari bulunamadi, once bunlari kaydedelim.")
        if not run_ayar_kaydet():
            print("Ayarlar kaydedilemedi, program sonlandiriliyor.", file=sys.stderr)
            sys.exit(1)

    config = read_config()
    il = config.get("Il")
    klinik = config.get("Klinik")
    hastane = config.get("Hastane")
    if not il or not klinik:
        print("config.local.ps1 icinde Il/Klinik degerleri eksik.", file=sys.stderr)
        sys.exit(1)

    run_randevu_ara(il, klinik, hastane=hastane, show=args.show)


if __name__ == "__main__":
    main()
