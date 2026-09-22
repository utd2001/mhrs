# MHRS Randevu Otomasyonu

MHRS (Merkezi Hekim Randevu Sistemi) üzerinde e-Devlet ile oturum açıp belirli bir il/klinik/hastane için randevu uygunluğunu kontrol eden ve en erken randevuyu bir mesaj kutusuyla bildiren otomasyon.

## İçindekiler

- [Dosyalar](#dosyalar)
- [Hızlı başlangıç](#hızlı-başlangıç)
- [Kurulum](#kurulum)
- [Ana akış (`mhrs.py`)](#ana-akış-mhrspy)
- [Randevu arama](#randevu-arama)
  - [Manuel kontrol](#manuel-kontrol)
  - [Otomatik saatlik kontrol](#otomatik-saatlik-kontrol-görev-zamanlayıcı)
- [Bilinen sınırlamalar](#bilinen-sınırlamalar)

## Dosyalar

| Dosya | Görev |
|---|---|
| `mhrs.py` | **Ana giriş noktası.** Çalıştırıldığında sırayla: gerekiyorsa e-Devlet girişi yaptırır, ayar yoksa Randevu Ara formunu açıp kullanıcının seçimlerini kaydeder (ilk kayıtta saatlik görevi de otomatik kurar), ardından `config.local.ps1`'deki değerlerle randevu aramasını çalıştırır. |
| `mhrs_login.py` | `mhrs.py`'nin kullandığı modül (oturum kontrolü + e-Devlet girişi). Tek başına da çalıştırılabilir. |
| `mhrs_ayar_kaydet.py` | `mhrs.py`'nin kullandığı modül. Randevu Ara formunu görünür tarayıcıda açar; İl/Klinik/Hastane'i kullanıcı elle seçer, Enter'a basınca seçilen değerler `config.local.ps1`'e kaydedilir. Tek başına da çalıştırılabilir. |
| `mhrs_randevu_ara.py` | `mhrs.py`'nin kullandığı modül. Randevu arama formunu otomatik doldurur, sonuçları listeler, en erken randevuyu msgbox ile gösterir. Tek başına da (parametrelerle) çalıştırılabilir. |
| `mhrs_common.psm1` | `install.ps1`, `uninstall.ps1` ve `mhrs_randevu_kontrol.ps1`'in ortak kullandığı PowerShell modülü (görev kurma/kaldırma, UTF-8 konsol ayarı, `mhrs.py` çağırma fonksiyonları). |
| `mhrs_randevu_kontrol.ps1` | `mhrs.py`'yi çalıştıran kısayol scripti (UTF-8 konsol ayarlarını yapar). `mhrs_common.psm1`'i kullanır. |
| `MHRS Randevu Kontrolu.bat` | `mhrs_randevu_kontrol.ps1`'i çift tıklamayla çalıştırmak için kısayol. |
| `MHRS Randevu Baslat.bat` | `mhrs.py`'yi PowerShell'e gerek kalmadan doğrudan çift tıklamayla çalıştırır. |
| `config.local.ps1` | **Repoya dahil değildir** (`.gitignore`). İl/Klinik/Hastane tercihlerinizi tutar; `mhrs_ayar_kaydet.py` tarafından otomatik oluşturulur. |
| `config.local.example.ps1` | `config.local.ps1` biçimine örnek şablon. `mhrs_ayar_kaydet.py` ayarları kaydedince otomatik silinir. |
| `install.ps1` | Saatlik Görev Zamanlayıcı görevini kurar (`mhrs_common.psm1` üzerinden). `mhrs.py` ayarları ilk kez kaydederken bunu otomatik çağırır; elle de çalıştırılabilir (`config.local.ps1` yoksa önce `mhrs.py`'yi çalıştırmanızı ister). |
| `uninstall.ps1` | Kurulu Görev Zamanlayıcı görevini kaldırır, `chrome_profile/` ve `config.local.ps1` verilerini siler (`mhrs_common.psm1` üzerinden). |
| `requirements.txt` | Python bağımlılıkları (selenium, webdriver-manager). |
| `chrome_profile/` | Kayıtlı tarayıcı oturumu/çerezleri. **Paylaşmayın**, kimlik bilgisi içerir. |

## Hızlı başlangıç

```powershell
pip install -r requirements.txt
python -X utf8 mhrs.py
```

`mhrs.py` gerekli tüm adımları (giriş, ayar kaydetme, arama) sırayla sizden ister; ilk çalıştırmadan sonra tekrar `python -X utf8 mhrs.py` demeniz yeterlidir.

## Kurulum

```powershell
pip install -r requirements.txt
```

Google Chrome ve Python'ın sistemde kurulu ve `python` komutunun PATH'te olması gerekir. İlk çalıştırmada `webdriver-manager` uygun chromedriver'ı otomatik indirir (internet bağlantısı gerekir).

## Ana akış (`mhrs.py`)

```powershell
python -X utf8 mhrs.py
```

`mhrs.py` çalıştırıldığında sırayla:

1. **Giriş kontrolü** — `chrome_profile/` yoksa görünür bir Chrome penceresi açılıp e-Devlet giriş sayfasına yönlendirilir. TC Kimlik No, şifre ve varsa SMS/OTP doğrulaması tamamen tarayıcıda elle girilir (hiçbir kimlik bilgisi terminale veya koda girmez). Giriş tamamlandıktan sonra terminalde Enter'a basılır. Oturum `chrome_profile/` içinde kalıcı olarak saklanır; bir daha bu adımı tekrarlamaya gerek kalmaz (oturum süresi dolana kadar).
2. **Ayar kontrolü** — `config.local.ps1` yoksa Randevu Ara formu görünür tarayıcıda açılır. İl, Klinik ve Hastane alanlarını kendiniz sitede seçersiniz, ardından terminale dönüp Enter'a basarsınız. O an formda seçili olan değerler otomatik olarak `config.local.ps1` dosyasına kaydedilir; dosyayı elle düzenlemenize gerek kalmaz. Ayarlar ilk kez başarıyla kaydedildiğinde saatlik [Görev Zamanlayıcı görevi](#otomatik-saatlik-kontrol-görev-zamanlayıcı) de otomatik kurulur (`install.ps1` arka planda çalıştırılır).
3. **Randevu arama** — `config.local.ps1`'deki İl/Klinik/Hastane değerleriyle otomatik arama çalıştırılır ([çalışma akışı](#çalışma-akışı) aşağıda anlatılıyor).

Ayarları değiştirmek isterseniz `config.local.ps1` dosyasını silip `mhrs.py`'yi tekrar çalıştırmanız yeterlidir; ayar adımı (ve görev kurulumu) yeniden tetiklenir.

## Randevu arama

Randevu iki şekilde kontrol edilebilir: elle, istediğiniz anda çalıştırarak (**Manuel kontrol**) veya arka planda saatte bir otomatik çalışan bir görevle (**Otomatik saatlik kontrol**).

### Manuel kontrol

En basit yol `mhrs.py`'yi doğrudan çalıştırmaktır (bkz. [Ana akış](#ana-akış-mhrspy)):

```powershell
python -X utf8 mhrs.py
```

`config.local.ps1` zaten varsa giriş/ayar adımları atlanır, doğrudan arama yapılır. `--show` ekleyerek aramayı görünür tarayıcı penceresinde çalıştırabilirsiniz:

```powershell
python -X utf8 mhrs.py --show
```

**Kısayolla çalıştırma:** `.\mhrs_randevu_kontrol.ps1` veya `MHRS Randevu Kontrolu.bat` dosyasına çift tıklayarak da aynı akış başlatılabilir.

**İleri düzey — parametrelerle tek seferlik arama:** `mhrs_randevu_ara.py`'yi doğrudan farklı İl/Klinik/Hastane/Hekim değerleriyle çalıştırmak isterseniz (kayıtlı ayarları değiştirmeden):

```powershell
python -X utf8 mhrs_randevu_ara.py --il "İSTANBUL" --klinik "Aile Hekimliği" --hastane "Fatih Sultan Mehmet"
```

Parametreler:

| Parametre | Zorunlu | Açıklama |
|---|---|---|
| `--il` | Evet | Form üzerindeki İl alanı. Örn: `"İSTANBUL"` |
| `--klinik` | Evet | Klinik/branş adı (kısmi eşleşme). Örn: `"Aile Hekimliği"` |
| `--hastane` | Hayır | Hastane adını filtreler (kısmi eşleşme). Örn: `"Fatih Sultan Mehmet"` |
| `--hekim` | Hayır | Hekim adını filtreler (kısmi eşleşme). Örn: `"Ad Soyad"` |
| `--show` | Hayır | Aramayı görünür tarayıcı penceresinde yapar (varsayılan: arka planda/headless). |

### Çalışma akışı

1. Kayıtlı profil ile (headless) Chrome açılır, oturumun açık olduğu varsayılır.
2. "Hastane Randevusu Al → Genel Arama" formu otomatik doldurulur (İl, Klinik, varsa Hastane) ve "Randevu Ara" ile arama yapılır.
3. Sonuç sayfaları (varsa birden fazla sayfa) gezilip tüm hekim/poliklinik kayıtları terminale yazdırılır.
4. En erken tarihli randevu bulunup bir **Evet/Hayır mesaj kutusunda** gösterilir:
   - **Hayır** → Program kapanır, hiçbir pencere açık kalmaz.
   - **Evet** → Görünür bir Chrome penceresi açılır, aynı form otomatik doldurulmuş halde bırakılır (kapanmaz); randevu işlemine elle devam edilebilir. Bu pencere kullanıcı kapatana kadar (en fazla 6 saat) açık kalır.

### Otomatik saatlik kontrol (Görev Zamanlayıcı)

`mhrs.py` ile ayarları ilk kez kaydettiğinizde ("MHRS Randevu Kontrolu" adlı) saatlik Görev Zamanlayıcı görevi otomatik olarak kurulur; ayrıca bir şey yapmanız gerekmez. Görev kayıt anından itibaren **her saat başı bir kez** çalışır (örn. kayıt 21:21 ise sonraki çalışmalar 22:21, 23:21, ... şeklinde, günün tam saatleri XX:00 değil) ve `mhrs_randevu_kontrol.ps1` üzerinden `mhrs.py`'yi headless modda çalıştırıp sonucu mesaj kutusuyla bildirir.

Görevi elle (yeniden) kurmak isterseniz — örneğin `uninstall.ps1` ile kaldırdıktan sonra `config.local.ps1` hâlâ mevcutsa, otomatik kurulum tetiklenmez çünkü `mhrs.py` sadece ayarları *ilk kez* kaydederken kurar:

```powershell
python -X utf8 mhrs.py                                          # once ayarlari kaydedin
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

Görev yalnızca kullanıcı oturumu açıkken (masaüstü etkileşimli oturumda) çalışır, çünkü mesaj kutusunun görünür olması buna bağlıdır.

#### Görevi yönetme

```powershell
# Durumu görüntüle
Get-ScheduledTask -TaskName "MHRS Randevu Kontrolu" | Get-ScheduledTaskInfo

# Devre dışı bırak
Disable-ScheduledTask -TaskName "MHRS Randevu Kontrolu"

# Tekrar etkinleştir
Enable-ScheduledTask -TaskName "MHRS Randevu Kontrolu"

# Elle bir kez çalıştır
Start-ScheduledTask -TaskName "MHRS Randevu Kontrolu"

# Tamamen kaldır
powershell -NoProfile -ExecutionPolicy Bypass -File .\uninstall.ps1
```

## Bilinen sınırlamalar

- Oturum süresi dolarsa (MHRS tarafında zaman aşımı) `chrome_profile/` klasörünü silip `mhrs.py`'yi tekrar çalıştırarak girişi yenileyin.
- "Evet" ile açılan görünür pencere açıkken (en fazla 6 saat), aynı `chrome_profile` klasörünü kullanan saatlik görev tetiklenirse profil kilidi çakışması yaşanabilir. Genelde randevu işlemi birkaç dakikada tamamlandığı için bu nadir bir durumdur.
- MHRS arayüzündeki metin/sınıf adları değişirse (site güncellemesi) form doldurma adımları güncellenmesi gerekebilir.
