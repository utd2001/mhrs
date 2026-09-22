# MHRS Randevu Otomasyonu

MHRS (Merkezi Hekim Randevu Sistemi) üzerinde e-Devlet ile oturum açıp
belirli bir il/klinik/hastane için randevu uygunluğunu kontrol eden ve
en erken randevuyu bir mesaj kutusuyla bildiren otomasyon.

## Dosyalar

| Dosya | Görev |
|---|---|
| `mhrs_login.py` | Chrome'u kalıcı profil (`chrome_profile/`) ile açar, oturum yoksa e-Devlet ile giriş yaptırır. |
| `mhrs_randevu_ara.py` | Randevu arama formunu otomatik doldurur, sonuçları listeler, en erken randevuyu msgbox ile gösterir. |
| `mhrs_randevu_kontrol.ps1` | `mhrs_randevu_ara.py`'yi sabit parametrelerle çalıştıran kısayol scripti. Gerçek İl/Klinik/Hastane değerlerini `config.local.ps1` varsa oradan okur, yoksa genel örnek değerleri kullanır. |
| `config.local.ps1` | **Repoya dahil değildir** (`.gitignore`). Kendi İl/Klinik/Hastane tercihlerinizi buraya yazın: `$Il = "..."`, `$Klinik = "..."`, `$Hastane = "..."`. |
| `config.local.example.ps1` | `config.local.ps1` için örnek şablon. Kopyalayıp kendi değerlerinizle doldurun: `Copy-Item config.local.example.ps1 config.local.ps1`. |
| `install.ps1` | `config.local.ps1` yoksa örnekten oluşturur ve saatlik Görev Zamanlayıcı görevini kurar. |
| `uninstall.ps1` | Kurulu Görev Zamanlayıcı görevini kaldırır, `chrome_profile/` ve `config.local.ps1` verilerini siler, `config.local.example.ps1`'i geri getirir. |
| `requirements.txt` | Python bağımlılıkları (selenium, webdriver-manager). |
| `chrome_profile/` | Kayıtlı tarayıcı oturumu/çerezleri. **Paylaşmayın**, kimlik bilgisi içerir. |

## Kurulum

```
pip install -r requirements.txt
```

Google Chrome ve Python'ın sistemde kurulu ve `python` komutunun PATH'te
olması gerekir. İlk çalıştırmada `webdriver-manager` uygun chromedriver'ı
otomatik indirir (internet bağlantısı gerekir).

### Kişisel arama ayarları (`.bat` / `.ps1` kısayolu için)

`MHRS Randevu Kontrolu.bat` dosyasını kullanacaksanız, önce kendi İl/Klinik/
Hastane tercihlerinizi tanımlayan bir `config.local.ps1` oluşturun:

```powershell
Copy-Item config.local.example.ps1 config.local.ps1
```

Sonra `config.local.ps1` içindeki `$Il`, `$Klinik`, `$Hastane` değerlerini
kendi aramanıza göre düzenleyin. Bu dosya `.gitignore` ile repo dışında
tutulur; oluşturmazsanız script genel örnek değerlerle çalışır.

## İlk giriş

```
python mhrs_login.py
```

Görünür bir Chrome penceresi açılır ve e-Devlet giriş sayfasına yönlendirilir.
TC Kimlik No, şifre ve varsa SMS/OTP doğrulaması tamamen tarayıcıda elle
girilir (hiçbir kimlik bilgisi terminale veya koda girmez). Giriş
tamamlandıktan sonra terminalde Enter'a basılır. Oturum `chrome_profile/`
içinde kalıcı olarak saklanır; bir daha bu adımı tekrarlamaya gerek kalmaz
(oturum süresi dolana kadar).

## Randevu arama

Türkçe karakterlerin (İ, Ö, Ş, Ç, Ğ, Ü) komut satırında doğru okunması için
**`-X utf8`** bayrağıyla çalıştırmak gerekir:

```
python -X utf8 mhrs_randevu_ara.py --il "İSTANBUL" --klinik "Aile Hekimliği" --hastane "Fatih Sultan Mehmet"
```

### Parametreler

| Parametre | Zorunlu | Açıklama |
|---|---|---|
| `--il` | Evet | Form üzerindeki İl alanı. Örn: `"İSTANBUL"` |
| `--klinik` | Evet | Klinik/branş adı (kısmi eşleşme). Örn: `"Aile Hekimliği"` |
| `--hastane` | Hayır | Hastane adını filtreler (kısmi eşleşme). Örn: `"Fatih Sultan Mehmet"` |
| `--hekim` | Hayır | Hekim adını filtreler (kısmi eşleşme). Örn: `"Ad Soyad"` |
| `--show` | Hayır | Aramayı görünür tarayıcı penceresinde yapar (varsayılan: arka planda/headless). |

### Çalışma akışı

1. Kayıtlı profil ile (headless) Chrome açılır, oturumun açık olduğu varsayılır.
2. "Hastane Randevusu Al → Genel Arama" formu otomatik doldurulur (İl, Klinik,
   varsa Hastane) ve "Randevu Ara" ile arama yapılır.
3. Sonuç sayfaları (varsa birden fazla sayfa) gezilip tüm hekim/poliklinik
   kayıtları terminale yazdırılır.
4. En erken tarihli randevu bulunup bir **Evet/Hayır mesaj kutusunda**
   gösterilir:
   - **Hayır** → Program kapanır, hiçbir pencere açık kalmaz.
   - **Evet** → Görünür bir Chrome penceresi açılır, aynı form otomatik
     doldurulmuş halde bırakılır (kapanmaz); randevu işlemine elle devam
     edilebilir. Bu pencere kullanıcı kapatana kadar (en fazla 6 saat) açık
     kalır.

## Otomatik saatlik kontrol (Görev Zamanlayıcı)

Görev Zamanlayıcı görevi repoyla birlikte gelmez, her makinede elle
kurulmalıdır. `install.ps1` çalıştırıldığında önce `config.local.ps1`
yoksa `config.local.example.ps1`'den oluşturur (ve örnek dosyayı siler),
ardından "MHRS Randevu Kontrolu" adında, kayıt anından itibaren **her
saat başı bir kez** çalışan bir görev oluşturur (örn. kayıt 21:21 ise
sonraki çalışmalar 22:21, 23:21, ... şeklinde, günün tam saatleri XX:00
değil). `config.local.ps1` içindeki İl/Klinik/Hastane parametreleriyle
`mhrs_randevu_ara.py`'yi headless modda çalıştırır ve sonucu mesaj
kutusuyla bildirir.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

Görev yalnızca kullanıcı oturumu açıkken (masaüstü etkileşimli oturumda)
çalışır, çünkü mesaj kutusunun görünür olması buna bağlıdır.

### Görevi yönetme

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

- Oturum süresi dolarsa (MHRS tarafında zaman aşımı) `mhrs_login.py`
  tekrar çalıştırılıp giriş yenilenmelidir.
- "Evet" ile açılan görünür pencere açıkken (en fazla 6 saat), aynı
  `chrome_profile` klasörünü kullanan saatlik görev tetiklenirse profil
  kilidi çakışması yaşanabilir. Genelde randevu işlemi birkaç dakikada
  tamamlandığı için bu nadir bir durumdur.
- MHRS arayüzündeki metin/sınıf adları değişirse (site güncellemesi)
  form doldurma adımları güncellenmesi gerekebilir.
