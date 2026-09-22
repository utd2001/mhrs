"""
MHRS (Merkezi Hekim Randevu Sistemi) - e-Devlet ile oturum acma ve
randevu uygunluk kontrolu otomasyonu.

Kullanim:
    python mhrs_login.py

Tarayici profili (cerezler dahil) bu klasordeki chrome_profile/ dizininde
saklanir. Bir kez giris yaptiktan sonra oturum acik kalir; sonraki
calistirmalarda tekrar TC/sifre girmeniz gerekmez.
"""

from __future__ import annotations

import sys
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

MHRS_VATANDAS_URL = "https://mhrs.gov.tr/vatandas/#/"
EDEVLET_TC_FIELD_ID = "tridField"
EDEVLET_PASSWORD_FIELD_ID = "egpField"
WAIT_TIMEOUT = 30

PROFILE_DIR = Path(__file__).resolve().parent / "chrome_profile"


def build_driver() -> webdriver.Chrome:
    PROFILE_DIR.mkdir(exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def is_logged_in(driver: webdriver.Chrome) -> bool:
    """Kalici profilden oturumun zaten acik olup olmadigini kontrol eder."""
    driver.get(MHRS_VATANDAS_URL)
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.edevlet-btn")))
        return False
    except TimeoutException:
        return True


def login_with_edevlet(driver: webdriver.Chrome) -> None:
    driver.get(MHRS_VATANDAS_URL)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    # MHRS vatandas portalindaki "e-Devlet ile Giris" butonuna tikla.
    edevlet_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.edevlet-btn"))
    )
    edevlet_button.click()

    # giris.turkiye.gov.tr sayfasina yonlendirilmeyi bekle.
    wait.until(EC.presence_of_element_located((By.ID, EDEVLET_TC_FIELD_ID)))

    print("Taraycida e-Devlet giris sayfasi acildi. TC Kimlik No, sifre ve "
          "varsa SMS/OTP dogrulamasini tarayicida elle tamamlayin.")
    input("Giris tamamlandiktan sonra devam etmek icin Enter'a basin...")

    wait.until(EC.url_contains("mhrs.gov.tr"))
    print("MHRS oturumu acildi.")


def main() -> None:
    driver = build_driver()
    try:
        if is_logged_in(driver):
            print("Kayitli profilden oturum zaten acik. Tekrar giris gerekmiyor.")
        else:
            login_with_edevlet(driver)

        input("Islem bitince tarayiciyi kapatmak icin Enter'a basin...")
    except TimeoutException:
        print("Sayfa elemanlari beklenen surede yuklenmedi. "
              "MHRS/e-Devlet sayfa yapisi degismis olabilir.", file=sys.stderr)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
