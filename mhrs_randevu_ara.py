"""
MHRS - kayitli profil ile oturum acip "Hastane Randevusu Al" > "Genel Arama"
akisini kullanarak belirli il + klinik (+ istege bagli hastane/hekim) icin
randevu sonuclarini listeler.

Kullanim:
    python -X utf8 mhrs_randevu_ara.py --il "İSTANBUL" --klinik "Aile Hekimliği" --hastane "Fatih Sultan Mehmet" [--hekim "Ad Soyad"] [--show]

Turkce karakterlerin (İ, Ö, Ş, ...) komut satirinda dogru okunmasi icin
"-X utf8" bayragiyla calistirmak onemlidir.

Onceden mhrs_login.py ile giris yapilmis olmasi ve chrome_profile/
dizininin bu klasorde bulunmasi gerekir.
"""

from __future__ import annotations

import argparse
import ctypes
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

MHRS_VATANDAS_URL = "https://mhrs.gov.tr/vatandas/#/"
WAIT_TIMEOUT = 30
PROFILE_DIR = Path(__file__).resolve().parent / "chrome_profile"

_TR_LOWER_MAP = str.maketrans("İIÖÜÇŞĞ", "iiöüçşğ")


def tr_lower(text: str) -> str:
    """Turkce 'I/İ' harflerini Python'un locale-bagimsiz .lower() metodunun
    yanlis cevirmesini (I -> i yerine i, İ -> i yerine i-with-dot) onlemek
    icin ozel eslemeyle kucuk harfe cevirir."""
    return text.translate(_TR_LOWER_MAP).lower()


def build_driver(headless: bool = True) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--window-size=1920,1080")
    if headless:
        options.add_argument("--headless=new")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def dismiss_modals(driver: webdriver.Chrome) -> None:
    for btn in driver.find_elements(By.CSS_SELECTOR, ".ant-modal-close, .ant-modal-footer button"):
        try:
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.5)
        except Exception:
            pass


def open_randevu_ara_form(driver: webdriver.Chrome) -> None:
    """Ana sayfadan 'Hastane Randevusu Al' > 'Genel Arama' formunu acar."""
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    driver.get(MHRS_VATANDAS_URL)
    time.sleep(2)
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
    time.sleep(2)


def select_tree_field(driver: webdriver.Chrome, placeholder_text: str, search_text: str | None, option_contains: str) -> None:
    """Ant Design tree-select alanini acar, gerekiyorsa arama yapar ve secenegi tiklar."""
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    field = wait.until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(),'{placeholder_text}')]")))
    driver.execute_script("arguments[0].click();", field)
    time.sleep(1)

    if search_text:
        search_fields = driver.find_elements(By.CSS_SELECTOR, "input.ant-select-search__field")
        visible_field = next((f for f in search_fields if f.is_displayed()), None)
        if visible_field:
            visible_field.send_keys(search_text)
            time.sleep(1.5)

    titles = driver.find_elements(By.CSS_SELECTOR, "span.ant-select-tree-title")
    for title in titles:
        if option_contains in title.text:
            driver.execute_script("arguments[0].click();", title)
            time.sleep(1.5)
            return

    raise NoSuchElementException(f"'{option_contains}' icermeyen secenek bulunamadi (alan: {placeholder_text}).")


def select_hastane_field(driver: webdriver.Chrome, hastane_contains: str) -> None:
    """Randevu Ara formundaki 'Hastane' alani (4. ant-select: dil, il, ilce, klinik, HASTANE)."""
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ant-select")))
    selects = driver.find_elements(By.CSS_SELECTOR, ".ant-select")
    hastane_field = selects[4]
    driver.execute_script("arguments[0].click();", hastane_field)
    time.sleep(1)

    search_fields = driver.find_elements(By.CSS_SELECTOR, "input.ant-select-search__field")
    visible_field = next((f for f in search_fields if f.is_displayed()), None)
    if visible_field:
        visible_field.send_keys(hastane_contains)
        time.sleep(1.5)

    titles = driver.find_elements(By.CSS_SELECTOR, "span.ant-select-tree-title")
    needle = tr_lower(hastane_contains)
    # En kisa (en spesifik olmayan / ana hastane) eslesmeyi tercih et:
    # semt/poliklinik alt kayitlari degil, ana hastane kaydi secilir.
    matches = [t for t in titles if needle in tr_lower(t.text)]
    if not matches:
        raise NoSuchElementException(f"'{hastane_contains}' icermeyen hastane bulunamadi.")
    best = min(matches, key=lambda t: len(t.text))
    driver.execute_script("arguments[0].click();", best)
    time.sleep(1.5)


def select_hekim_field(driver: webdriver.Chrome, hekim_contains: str) -> None:
    """Hekim alani basit bir Ant Select (tree degil); acilinca menu item'lardan secilir."""
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    selects = driver.find_elements(By.CSS_SELECTOR, ".ant-select")
    hekim_field = selects[6]
    driver.execute_script("arguments[0].click();", hekim_field)
    time.sleep(1)

    needle = tr_lower(hekim_contains)
    items = driver.find_elements(By.CSS_SELECTOR, ".ant-select-dropdown-menu-item")
    for item in items:
        if needle in tr_lower(item.text):
            driver.execute_script("arguments[0].click();", item)
            time.sleep(1)
            return

    raise NoSuchElementException(f"'{hekim_contains}' icermeyen hekim bulunamadi.")


def search_randevu(
    driver: webdriver.Chrome,
    il: str,
    klinik: str,
    hastane: str | None = None,
    hekim: str | None = None,
) -> str:
    open_randevu_ara_form(driver)
    select_tree_field(driver, "İl Seçiniz", None, il)
    select_tree_field(driver, "Klinik Seçiniz", klinik, klinik)

    if hastane:
        select_hastane_field(driver, hastane)

    if hekim:
        select_hekim_field(driver, hekim)

    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    search_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Randevu Ara')]")))
    driver.execute_script("arguments[0].click();", search_btn)
    time.sleep(4)

    return collect_all_pages_text(driver)


def collect_all_pages_text(driver: webdriver.Chrome) -> str:
    """Sonuc listesindeki tum sayfalari gezip metinlerini birlestirir."""
    app = driver.find_element(By.ID, "vatandasApp")
    texts = [app.text]

    pagination = driver.find_elements(By.CSS_SELECTOR, ".ant-pagination")
    if not pagination:
        return texts[0]

    page_items = pagination[0].find_elements(By.CSS_SELECTOR, "li.ant-pagination-item")
    total_pages = len(page_items)

    for page_num in range(2, total_pages + 1):
        page_btn = driver.find_element(
            By.CSS_SELECTOR, f".ant-pagination li.ant-pagination-item-{page_num}"
        )
        driver.execute_script("arguments[0].click();", page_btn)
        time.sleep(2.5)
        app = driver.find_element(By.ID, "vatandasApp")
        texts.append(app.text)

    return "\n".join(texts)


def parse_results(text: str) -> list[dict]:
    """'Hastane' sonuc sayfasinin metnini hekim bazli kayitlara ayirir."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    records = []
    i = 0
    while i < len(lines):
        if lines[i] == "En Erken Tarih" and i >= 1:
            hekim = lines[i - 1]
            tarih = lines[i + 1] if i + 1 < len(lines) else ""
            kalan = lines[i + 2] if i + 2 < len(lines) else ""
            hastane = lines[i + 3] if i + 3 < len(lines) else ""
            klinik = lines[i + 4] if i + 4 < len(lines) else ""
            poliklinik = lines[i + 5] if i + 5 < len(lines) else ""
            records.append({
                "hekim": hekim,
                "en_erken_tarih": tarih,
                "kalan": kalan,
                "hastane": hastane,
                "klinik": klinik,
                "poliklinik": poliklinik,
            })
        i += 1
    return records


def parse_tarih(tarih: str) -> datetime | None:
    """'07.10.2026 Çarşamba' -> datetime(2026, 10, 7). Parse edilemezse None doner."""
    try:
        gun_ay_yil = tarih.split(" ")[0]
        return datetime.strptime(gun_ay_yil, "%d.%m.%Y")
    except (ValueError, IndexError):
        return None


def en_erken_kayit(records: list[dict]) -> dict | None:
    dated = [(parse_tarih(r["en_erken_tarih"]), r) for r in records]
    dated = [(d, r) for d, r in dated if d is not None]
    if not dated:
        return None
    return min(dated, key=lambda pair: pair[0])[1]


def show_msgbox(title: str, message: str) -> None:
    """Windows'ta senkron bir bilgi mesaj kutusu gosterir (kullanici Tamam'a basana kadar bekler)."""
    MB_OK = 0x0
    MB_ICONINFORMATION = 0x40
    MB_TOPMOST = 0x40000
    ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK | MB_ICONINFORMATION | MB_TOPMOST)


def ask_yesno_msgbox(title: str, message: str) -> bool:
    """Evet/Hayir mesaj kutusu gosterir. Evet -> True, Hayir -> True degil (False)."""
    MB_YESNO = 0x4
    MB_ICONQUESTION = 0x20
    MB_TOPMOST = 0x40000
    IDYES = 6
    result = ctypes.windll.user32.MessageBoxW(0, message, title, MB_YESNO | MB_ICONQUESTION | MB_TOPMOST)
    return result == IDYES


def run_randevu_ara(
    il: str,
    klinik: str,
    hastane: str | None = None,
    hekim: str | None = None,
    show: bool = False,
) -> None:
    """Randevu aramasini calistirir; en erken randevuyu msgbox ile bildirir.

    Onceden mhrs_login.py / mhrs.py ile giris yapilmis ve chrome_profile/
    dizininin bu klasorde bulunmasi gerekir.
    """
    driver = build_driver(headless=not show)
    driver_open = True
    try:
        text = search_randevu(driver, il, klinik, hastane=hastane, hekim=hekim)
        records = parse_results(text)

        if not records:
            print("Uygun sonuc bulunamadi.")
            show_msgbox("MHRS Randevu Sonucu", "Uygun randevu bulunamadi.")
            return

        print(f"{len(records)} sonuc bulundu:\n")
        for r in records:
            print(f"- {r['hekim']}  |  {r['en_erken_tarih']} ({r['kalan']})")
            print(f"    {r['hastane']}")
            print(f"    {r['klinik']} - {r['poliklinik']}\n")

        en_erken = en_erken_kayit(records)
        if en_erken:
            mesaj = (
                f"En erken randevu:\n\n"
                f"Hekim: {en_erken['hekim']}\n"
                f"Tarih: {en_erken['en_erken_tarih']} ({en_erken['kalan']})\n"
                f"Hastane: {en_erken['hastane']}\n"
                f"Klinik: {en_erken['klinik']}\n"
                f"Poliklinik: {en_erken['poliklinik']}\n\n"
                f"Randevu almak icin siteyi acmak ister misiniz?"
            )
            # Once headless tarayiciyi kapat, sonra soruyu sor - Evet derse
            # yeni bir GORUNUR tarayici acip formu tekrar doldurup oyle birakacagiz.
            driver.quit()
            driver_open = False

            acilsin_mi = ask_yesno_msgbox("MHRS - En Erken Randevu", mesaj)
            if acilsin_mi:
                visible_driver = build_driver(headless=False)
                search_randevu(visible_driver, il, klinik, hastane=hastane, hekim=hekim)
                # ChromeDriver, kendisine baglanan Python/WebDriver client'i
                # kapanınca (surec bitince VEYA baglanti kesilince) yonettigi
                # Chrome penceresini de otomatik kapatir. Pencereyi acik
                # tutmak icin Python surecinin kendisini canli tutup
                # chromedriver baglantisini koparmiyoruz. Kullanici pencereyi
                # kendi kapatana kadar burada bekleriz (en fazla 6 saat).
                print("Tarayici penceresi acik birakildi. Kapatmak icin pencereyi "
                      "elle kapatabilir veya bu programi sonlandirabilirsiniz.")
                max_wait_seconds = 6 * 60 * 60
                elapsed = 0
                while elapsed < max_wait_seconds:
                    try:
                        _ = visible_driver.title  # pencere hala acik mi kontrol
                    except Exception:
                        break
                    time.sleep(5)
                    elapsed += 5
    except TimeoutException:
        print("Sayfa beklenen surede yuklenmedi. Once mhrs_login.py ile giris yapin.")
        show_msgbox("MHRS Randevu Sonucu", "Sayfa beklenen surede yuklenmedi. Once mhrs_login.py ile giris yapin.")
    except NoSuchElementException as e:
        print(f"Form doldurulurken hata: {e}")
        show_msgbox("MHRS Randevu Sonucu", f"Form doldurulurken hata olustu:\n{e}")
    finally:
        if driver_open:
            driver.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="MHRS randevu uygunluk kontrolu")
    parser.add_argument("--il", required=True, help='Ornek: "İSTANBUL"')
    parser.add_argument("--klinik", required=True, help='Ornek: "Aile Hekimliği"')
    parser.add_argument("--hastane", default=None, help='Formdaki Hastane alanini bu metinle doldurur. Ornek: "Fatih Sultan Mehmet"')
    parser.add_argument("--hekim", default=None, help='Formdaki Hekim alanini bu metinle doldurur. Ornek: "Ad Soyad"')
    parser.add_argument("--show", action="store_true", help="Tarayiciyi gorunur modda calistir")
    args = parser.parse_args()

    run_randevu_ara(args.il, args.klinik, hastane=args.hastane, hekim=args.hekim, show=args.show)


if __name__ == "__main__":
    main()
