# SEIS IT Workshop — OpenCV Atölyesi (4 Saatlik Uygulama Planı)

**Tarih:** 27 Kasım Cuma  
**Saat:** 16:00 – 20:00 (Toplam 240 dakika = 210 dk eğitim/uygulama/yarışma + 30 dk mola)  
**Konum:** Bilgisayar ve Bilişim Bilimleri Fakültesi, 1108 Numaralı Sınıf  
**Kaynak Repo:** `vision-workshop` (*VISION LAB — Kameradan Etkileşime*)

---

## 1. Mevcut Projenin İncelenmesi ve 4 Saate İndirgeme Stratejisi

`vision-workshop` klasörü aslında **12 saatlik (4 × 3 saat)** üniversite dersi olarak tasarlanmış (ayrıca 6 saatlik kısa sürümü var). İçinde 10 aşamalı Python örneği (`examples/01–10`), 24 sahnelik React web sunumu (`presentation/`), 18 sayfalık öğrenci raporu ve 4 modlu birleşik uygulama (`src/main.py`) bulunuyor.

4 saatlik bir atölyede hepsini kodlatmaya çalışmak tempoyu düşürür. Bu yüzden projeyi **2 ana uygulamalı proje + 1 final vitrin demosu + 1 ödüllü yarışma** şeklinde keskinleştiriyoruz:

| Mevcut Modül (`vision-workshop`) | 4 Saatlik Atölyedeki Rolü | İlgili Dosyalar |
|---|---|---|
| **Giriş & Vizyon** (Yeni) | **Sunum:** OpenCV nedir, araçları, dünya devleri nerede kullanıyor? | `Gemini/index.html` |
| **Temeller (01–03)** | **Hızlı Uygulama:** Kamera akışı, BGR/HSV, Gaussian Blur & Canny/Eşik | `examples/01_kamera.py`, `02_piksel_renk.py`, `03_filtre_esik.py` |
| **Proje 1: Akıllı Yüz & Göz Analizi** | **Uygulamalı Proje 1:** Yüz tespiti, 468 landmark, göz kırpma (EAR) & baş pozu | `examples/04_yuz_tespiti.py`, `06_yuz_geometrisi.py` |
| **Proje 2: Temassız El Jestleri** | **Uygulamalı Proje 2:** 21 el noktası, pinch jesti ile ekranda kontrol/sürükleme | `examples/07_el_noktalari.py`, `08_el_jestleri.py` |
| **Cilt Analizi & Birleşik Uygulama** | **Sadece Canlı Demo (5 dk):** "Bu temellerle neler birleşiyor?" vitrini | `examples/10_cilt_analizi.py`, `src/main.py` |
| **Ödüllü Yarışma (Kahoot Tarzı)** | **Etkileşimli Kapanış:** 12–15 soruluk hızlı yarışma ve ödül | *(Bir sonraki adımda hazırlanacak)* |

> **Neden bu 2 proje?**
> - **Proje 1 (Yüz & Göz):** Etkinlik afişindeki göz + yeşil landmark ağı görseliyle birebir örtüşür. Katılımcılar kendi göz kırpmalarını anlık saydırınca hemen bağlanırlar.
> - **Proje 2 (El Jestleri):** Kameraya elini kaldırıp ekrandaki sürgüyü/kutuyu temassız hareket ettirmek atölyenin en yüksek "vay be!" anıdır.

---

## 2. Dakika Dakika 4 Saatlik Atölye Akışı (16:00 – 20:00)

| Saat | Süre | Bölüm | İçerik & Kullanılacak Materyal | Önerilen Rol Dağılımı |
|---|---|---|---|---|
| **16:00 – 16:15** | 15 dk | **Açılış & Kurulum Kontrolü** | Hoş geldiniz, SEIS tanıtımı, gizlilik notu (görüntü kaydedilmez). Önceden kurmayanlar için hızlı kontrol (`check_setup.py --kamera`). | Sunucu A + Destek Ekibi |
| **16:15 – 16:45** | 30 dk | **Bölüm 1: OpenCV Nedir? & Dünya Devleri** | `Gemini/index.html` üzerinden animasyonlu sunum: Bilgisayarlı görü nedir, piksel matrisleri, OpenCV araçları, Tesla/Hawk-Eye/Sağlık/Üretim kullanım örnekleri ve canlı filtre demosu. | Sunucu A (veya B) |
| **16:45 – 17:20** | 35 dk | **Bölüm 2: OpenCV Temelleri (Canlı Kodlama)** | `01_kamera.py` (kamera döngüsü, FPS), `02_piksel_renk.py` (BGR vs RGB tuzağı, HSV), `03_filtre_esik.py` (Gaussian Blur, eşikleme, kenar/kontur). | Sunucu A |
| **17:20 – 17:35** | 15 dk | **1. Mola** | Çay/kahve + kurulum sorunu yaşayan öğrencilere birebir destek. | Tüm Ekip |
| **17:35 – 18:25** | 50 dk | **Proje 1: Akıllı Yüz Takibi & Göz Kırpma (EAR)** | OpenCV + MediaPipe Tasks API farkı (5 dk) → `04_yuz_tespiti.py` ve `06_yuz_geometrisi.py` üzerinden canlı yüz ağı, göz kırpma oranı (EAR) ve baş yönelimi uygulaması. | Sunucu A *(veya Sunucu B)* |
| **18:25 – 18:40** | 15 dk | **2. Mola** | Kısa dinlenme + katılımcıların ilk projelerini test etmesi. | Tüm Ekip |
| **18:40 – 19:30** | 50 dk | **Proje 2: Temassız El Jestleri Kontrolü** | `07_el_noktalari.py` (21 eklem noktası, parmak açıları) → `08_el_jestleri.py` (pinch mesafesi, histerezis ile kararlı komut, temassız sürgü ve kutu sürükleme). | Sunucu B *(veya Sunucu A)* |
| **19:30 – 19:40** | 10 dk | **Final Vitrin Demosu** | `src/main.py` ile yüz + el + cilt analizi modüllerinin tek uygulamada birleşiminin canlı gösterimi; GitHub reposu ve evde devam önerileri. | Sunucu A + B |
| **19:40 – 20:00** | 20 dk | **Ödüllü Yarışma & Kapanış** | Kahoot tarzı interaktif OpenCV bilgi yarışması, ödül takdimi, toplu fotoğraf ve geri bildirim. | Tüm Ekip |

---

## 3. Ekip İçi Sunum Senaryoları

- **Senaryo 1 (İki Eğitmenli — En Dinamik):**
  - **1. Eğitmen:** Açılış + OpenCV Temelleri + Proje 1 (Yüz & Göz Analizi)
  - **2. Eğitmen:** OpenCV Nedir & Sektör Örnekleri + Proje 2 (El Jestleri) + Yarışma Moderatörlüğü
- **Senaryo 2 (Tek Ana Kodlayıcı + 1 Teori/Sunum Eğitmeni):**
  - **Anlatıcı:** `Gemini/index.html` ile teori, şirket örnekleri, algoritma mantığı ve yarışma yönetimi.
  - **Kodlayıcı:** Canlı kodlama (Temeller + Proje 1 + Proje 2) ve final demo.

---

## 4. Etkinlik Öncesi Kritik Hatırlatmalar (Zaman Kazanmak İçin)

1. **Ön Kurulum Duyurusu:** Katılımcılara 1 gün önceden `docs/HAZIRLIK_KONTROL_LISTESI.md` adımlarını (Python 3.12 + `pip install -r requirements.txt` + `python scripts/download_models.py`) yapıp gelmeleri duyurulmalı; aksi halde 150 MB indirme sınıf internetini kilitleyebilir.
2. **USB Yedek:** `models/` klasöründeki indirilmiş modellerin bir yedeği 2 adet USB bellekte sınıfta hazır bulundurulmalı.
3. **Kamerasız Katılım:** Kamerası olmayan veya açmak istemeyen öğrenciler için `--source video.mp4` ve `presentation/` içindeki "Örnek gösterim" modu hazır.
4. **Siyah Kamera Sorunu (Mac):** iPhone Süreklilik Kamerası devreye girerse `--source auto` veya `--source 1` parametresi kullanılır.
