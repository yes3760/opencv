# VISION LAB — Eğitim öncesi hazırlık kontrol listesi

Bu liste eğitimden önce tamamlanır. Kurulum yaklaşık 15-20 dakika sürer, 150 MB indirme ve 500 MB disk
alanı gerektirir. İnternet yalnızca kurulum sırasında gerekir. Ayrıntılı adımlar öğrenci raporunun
D bölümündedir.

## Gerekenler

- Dahili kamerası olan dizüstü bilgisayar: Windows 10/11 (x64) veya macOS 13 Ventura ve üstü
- Python 3.12 (python.org veya Homebrew)
- Ücretli hesap, API anahtarı, ayrı ekran kartı veya ek donanım gerekmez

## Adımlar

- [ ] **Python 3.12 kurulu.** Kontrol: `python3.12 --version` (Windows: `py -3.12 --version`)
- [ ] **İşlemci türü biliniyor (yalnızca Mac).** `uname -m` komutu `arm64` veya `x86_64` yazar.
- [ ] **Proje klasörü indirildi** ve terminal bu klasörde açıldı.
- [ ] **Sanal ortam oluşturuldu ve etkinleştirildi.**
  - macOS: `python3.12 -m venv .venv` ardından `source .venv/bin/activate`
  - Windows: `py -3.12 -m venv .venv` ardından `.venv\Scripts\activate.bat`
- [ ] **Paketler kuruldu:** `pip install -r requirements.txt`
  (Intel işlemcili Mac: `pip install -r requirements-intel-mac.txt`)
- [ ] **Modeller indirildi:** `python scripts/download_models.py` üç model için `[tamam]` yazdı.
- [ ] **Kamera izni verildi.**
  - macOS: Sistem Ayarları > Gizlilik ve Güvenlik > Kamera bölümünde programı başlatan uygulama
    (Terminal, VS Code vb.) açık.
  - Windows: Ayarlar > Gizlilik ve güvenlik > Kamera bölümünde masaüstü uygulamalarının erişimi açık.
- [ ] **Kontrol tamam:** `python scripts/check_setup.py --kamera` sonunda "Ortam hazır" yazdı ve
  "Görüntü parlaklığı" satırı `[tamam]` gösterdi.
- [ ] **İlk örnek açıldı:** `python examples/01_kamera.py` pencerede kamera görüntüsünü gösterdi;
  `q` ile kapandı.
- [ ] Zoom, Teams gibi kamerayı kullanan uygulamalar kapalı.
- [ ] Şarj aleti hazır.

## Sık görülen durumlar

| Durum | Çözüm |
|---|---|
| Görüntü siyah | Bilgisayarda birden fazla kamera olabilir (ör. Mac'te iPhone). Varsayılan `--source auto` görüntü veren kamerayı seçer; elle `--source 1` denenir. Mercek kapağı kontrol edilir. |
| "Kamera açılamadı" | Kamera başka uygulamada açık olabilir veya izin verilmemiştir. |
| `No matching distribution found for mediapipe` | Python 3.12 kullanılır; Intel Mac'te `requirements-intel-mac.txt` kurulur. |
| `CERTIFICATE_VERIFY_FAILED` | Komutlar sanal ortam etkinken çalıştırılır. |
| PowerShell etkinleştirmeyi engelliyor | `cmd` kullanılır veya yalnızca o pencere için `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`. |

## Kamera kullanmak istemeyenler için

Kamera kullanımı gönüllüdür. Kendi çektiğiniz veya kullanma hakkınız olan bir video ya da fotoğraf
`--source dosya.mp4` ile verilebilir; sunumdaki "Örnek gösterim" modu da izlenebilir. Uygulama
görüntü kaydetmez ve hiçbir sunucuya göndermez.
