# VISION LAB — Kameradan Etkileşime

OpenCV, NumPy ve MediaPipe Tasks API ile yüz, el ve cilt görünümü analizi; üniversite topluluğu için
aşamalı eğitim projesi. Ayrıntılı anlatım: `docs/OGRENCI_RAPORU.md` (PDF: `docs/OGRENCI_RAPORU.pdf`).

## Kurulum (Python 3.12)

```bash
python3.12 -m venv .venv            # Windows: py -3.12 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate.bat
pip install -r requirements.txt     # Intel Mac: requirements-intel-mac.txt
python scripts/download_models.py   # modeller SHA-256 ile doğrulanır
python scripts/check_setup.py --kamera
```

## Çalıştırma

```bash
python examples/01_kamera.py        # aşamalar 01-10, examples/ klasöründe
python src/main.py                  # birleşik uygulama (1-4 mod, boşluk: cilt analizi, q: çıkış)
python src/main.py --source 1       # belirli bir kamera (varsayılan: auto, görüntü veren ilk kamera)
python src/main.py --source video.mp4   # kamerasız katılım
python -m pytest -q                 # testler (requirements-dev.txt)
```

## Web sunumu (eğitmen için)

```bash
cd presentation
npm install
npm run dev                         # http://localhost:5173 — kamera yalnızca localhost/HTTPS'te açılır
npm run build                       # üretim derlemesi: presentation/dist
npm run notes                       # docs/EGITMEN_NOTLARI.md dosyasını sahne verisinden üretir
```

Modeller ve MediaPipe wasm dosyaları `npm run setup` ile `public/` klasörüne kopyalanır; sunum
kurulumdan sonra internetsiz çalışır. Kamera görüntüsü hiçbir sunucuya gönderilmez.

## Organizasyon bilgileri

Üniversite, topluluk, eğitmen, tarih ve iletişim bilgileri yalnızca `workshop.config.json` dosyasından
düzenlenir. Rapor PDF'i yeniden üretmek için: `python docs/tools/build_report.py` (pandoc + Chrome).

## Belgeler

| Dosya | İçerik |
|---|---|
| `docs/OGRENCI_RAPORU.md` / `.pdf` | Öğrenci raporu (18 sayfa) |
| `docs/EGITMEN_NOTLARI.md` | Oturum akışı ve sahne sahne anlatım notları |
| `docs/HAZIRLIK_KONTROL_LISTESI.md` | Eğitim öncesi kurulum listesi |
| `docs/KAYNAKCA_VE_LISANSLAR.md` | Kaynaklar ve üçüncü taraf lisans notları |
| `docs/DOGRULAMA_RAPORU.md` | Yapılan ve yapılamayan doğrulamalar |

## Sık karşılaşılan durum: siyah görüntü

Bilgisayarda birden fazla kamera varsa (ör. Mac'te iPhone Süreklilik Kamerası) 0 numara dahili kamera
olmayabilir. Varsayılan `--source auto` görüntü veren kamerayı seçer; sunumda canlı demonun altındaki
listeden kamera değiştirilebilir.

Eğitim amaçlı görüntü analizi; tıbbi tanı değildir.
