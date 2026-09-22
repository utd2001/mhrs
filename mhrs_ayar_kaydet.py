"""
MHRS - Randevu Ara formunu tarayicida GORUNUR sekilde acar; Il, Klinik ve
Hastane alanlarini kullanici elle doldurur. Terminalde Enter'a basildiginda
formda o an secili olan degerler okunup config.local.ps1 dosyasina yazilir.

Bu dosya mhrs.py tarafindan modul olarak kullanilir (run_ayar_kaydet()).
Tek basina da calistirilabilir:
    python -X utf8 mhrs_ayar_kaydet.py

chrome_profile/ dizini yoksa (henuz giris yapilmamissa) once e-Devlet giris
akisi otomatik calistirilir, ardindan Randevu Ara formu acilir.
"""

from __future__ import annotations

import sys
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from mhrs_login import is_logged_in, login_with_edevlet

MHRS_VATANDAS_URL = "https://mhrs.gov.tr/vatandas/#/"
WAIT_TIMEOUT = 30
PROFILE_DIR = Path(__file__).resolve().parent / "chrome_profile"
CONFIG_PATH = Path(__file__).resolve().parent / "config.local.ps1"

# Randevu Ara formundaki .ant-select sirasi: 0=Dil, 1=Il, 2=Ilce, 3=Klinik, 4=Hastane
SELECT_INDEX = {"il": 1, "klinik": 3, "hastane": 4}


def build_driver() -> webdriver.Chrome:
    PROFILE_DIR.mkdir(exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def ensure_logged_in(driver: webdriver.Chrome) -> None:
    if is_logged_in(driver):
        print("Kayitli profilden oturum zaten acik.")
        return
    login_with_edevlet(driver)


def dismiss_modals(driver: webdriver.Chrome) -> None:
    for btn in driver.find_elements(By.CSS_SELECTOR, ".ant-modal-close, .ant-modal-footer button"):
        try:
            driver.execute_script("arguments[0].click();", btn)
        except Exception:
            pass


def open_randevu_ara_form(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    driver.get(MHRS_VATANDAS_URL)
    dismiss_modals(driver)

    hastane_card_title = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Hastane Randevusu Al')]"))
    )
    card = hastane_card_title.find_element(By.XPATH, './ancestor::div[contains(@class, "card")][1]')
    driver.execute_script("arguments[0].click();", card)

    genel_arama = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Genel Arama')]"))
    )
    driver.execute_script("arguments[0].click();", genel_arama)


def read_selected_value(driver: webdriver.Chrome, field_name: str) -> str:
    """Verilen .ant-select alaninin o an secili (kapali kutuda gorunen) metnini okur."""
    index = SELECT_INDEX[field_name]
    selects = driver.find_elements(By.CSS_SELECTOR, ".ant-select")
    if index >= len(selects):
        raise NoSuchElementException(f"'{field_name}' alani formda bulunamadi.")
    field = selects[index]
    selected = field.find_elements(By.CSS_SELECTOR, ".ant-select-selection-selected-value")
    text = selected[0].text.strip() if selected else ""
    if not text:
        raise NoSuchElementException(f"'{field_name}' alani doldurulmamis gorunuyor.")
    return text


def write_config(il: str, klinik: str, hastane: str) -> None:
    content = (
        f'$Il = "{il}"\n'
        f'$Klinik = "{klinik}"\n'
        f'$Hastane = "{hastane}"\n'
    )
    CONFIG_PATH.write_text(content, encoding="utf-8-sig")


def run_ayar_kaydet() -> bool:
    """Formu tarayicida acar, kullanicinin secimlerini config.local.ps1'e kaydeder.

    Basariyla kaydedilirse True, hata olursa False doner.
    """
    driver = build_driver()
    try:
        ensure_logged_in(driver)
        open_randevu_ara_form(driver)

        print("Tarayicida Il/Klinik/Hastane secin, sonra Enter'a basin.")
        print("NOT: 'Randevu Ara' butonuna basmayin.")
        input()

        il = read_selected_value(driver, "il")
        klinik = read_selected_value(driver, "klinik")
        hastane = read_selected_value(driver, "hastane")

        write_config(il, klinik, hastane)

        print("config.local.ps1 kaydedildi:")
        print(f"  Il      : {il}")
        print(f"  Klinik  : {klinik}")
        print(f"  Hastane : {hastane}")
        return True
    except TimeoutException:
        print("Sayfa beklenen surede yuklenmedi. MHRS/e-Devlet sayfa yapisi degismis olabilir.", file=sys.stderr)
        return False
    except NoSuchElementException as e:
        print(f"Ayarlar okunamadi: {e}", file=sys.stderr)
        print("Uc alan da secili mi kontrol edip, 'Randevu Ara'ya basmadan tekrar deneyin.", file=sys.stderr)
        return False
    finally:
        driver.quit()


if __name__ == "__main__":
    run_ayar_kaydet()
