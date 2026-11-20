---
title: "VISION LAB — Kameradan Etkileşime"
subtitle: "OpenCV ile Yüz, El ve Cilt Görünümü Analizi · Eğitim ve Proje Raporu"
lang: tr
---

::: {.kunye}
**Topluluk:** <span class="placeholder">[Topluluk adı]</span> · **Üniversite:** <span class="placeholder">[Üniversite adı]</span> · **Eğitmen:** <span class="placeholder">[Eğitmen adı]</span><br>
**Tarih:** <span class="placeholder">[Tarih]</span> · **Yer:** <span class="placeholder">[Yer]</span> · **İletişim:** <span class="placeholder">[İletişim]</span> · **Destekleyen:** <span class="placeholder">[Destekleyen kurum (varsa)]</span><br>
**Proje deposu:** <span class="placeholder">[Depo bağlantısı]</span> · **Rapor sürümü:** 1.0 · **Araştırma ve kontrol tarihi:** 19 Ekim 2026
:::

::: {.uyari}
Bu eğitimdeki cilt bölümü eğitim amaçlı görüntü analizidir; tıbbi tanı değildir. Kamera kullanımı
gönüllüdür. Uygulama görüntü kaydetmez ve hiçbir görüntüyü harici bir sunucuya göndermez.
:::

# A. Eğitimin amacı ve ortaya çıkacak uygulama

Bu eğitimde bir dizüstü bilgisayarın dahili kamerasından gelen görüntünün nasıl sayılara, ölçümlere ve
etkileşime dönüştüğü adım adım incelenecektir. Amaç yalnızca etkileyici bir demo izlemek değil, her
adımda görüntünün ne olduğunu, hangi işlemden geçtiğini ve sonucun neyi ölçüp neyi ölçmediğini
anlamaktır.

Eğitim boyunca tek bir proje aşama aşama büyütülür. Her aşama, `examples/` klasöründe tek başına
çalışabilen bir dosyaya karşılık gelir ve sonunda bütün modüller `src/main.py` içinde birleşir.

| Aşama | Konu | Dosya | Oturum |
|---|---|---|---|
| 1 | Kamera görüntüsü | `examples/01_kamera.py` | 1 |
| 2 | Pikseller ve renk uzayları | `examples/02_piksel_renk.py` | 1 |
| 3 | ROI, filtre, eşik, morfoloji, kontur | `examples/03_filtre_esik.py` | 1 |
| 4 | Yüz tespiti ve işaret noktaları | `examples/04_yuz_tespiti.py` | 2 |
| 5 | Yüz takibi ve hareket izi | `examples/05_yuz_takip.py` | 2 |
| 6 | Yüz geometrisi ve hareketleri | `examples/06_yuz_geometrisi.py` | 2 |
| 7 | El işaret noktaları | `examples/07_el_noktalari.py` | 3 |
| 8 | Kararlı jestler ve etkileşim | `examples/08_el_jestleri.py` | 3 |
| 9 | Cilt analiz bölgeleri | `examples/09_cilt_bolgeleri.py` | 4 |
| 10 | Açıklanabilir cilt görünümü analizi | `examples/10_cilt_analizi.py` | 4 |
| 11 | Birleşik uygulama | `src/main.py` | 4 |

Uygulama sonunda kamera görüntüsü üzerinde yüz noktaları ve hareket izi görülecek, göz ve ağız
açıklığı ile yaklaşık baş yönelimi ölçülecek, el hareketleriyle uygulama içindeki düğmeler ve sürgü
kontrol edilebilecek ve kalite kontrolünden geçen tek bir kareden açıklanabilir cilt görünümü
haritaları üretilecektir.

## Eğitim takvimi

Varsayılan plan 4 oturumdan oluşur. Her oturum 75 dakika eğitim ve uygulama, 15 dakika ara ve 90
dakika eğitim ve uygulamadan oluşur; bir oturum 180 dakikadır. Toplam süre 4 × 180 = **720 dakika
(12 saat)**; bunun **660 dakikası (11 saat)** eğitim ve uygulama, **60 dakikası** aradır.

| Oturum, çıktı ve aşama | Birinci bölüm (75 dk) | İkinci bölüm (90 dk, 15 dk aradan sonra) |
|---|---|---|
| **1. Temeller**<br>Çıktı: Görüntüyü dizi olarak okuyup kural tabanlı bir işleme hattı kurmak<br>Aşama: 1-3 | 0:00 Tanışma, gizlilik ve gönüllülük (10)<br>0:10 Kurulum kontrolü (20)<br>0:30 Kamera döngüsü ve FPS (20)<br>0:50 NumPy dizisi, BGR/RGB, gri, HSV, LAB (25) | 1:30 ROI ve yeniden boyutlandırma (20)<br>1:50 Gaussian bulanıklık, eşik, Otsu (25)<br>2:15 Morfoloji ve kontur (20)<br>2:35 FPS, gecikme; kural tabanlı ve öğrenilmiş yöntem (15)<br>2:50 Öğrenci deneyi ve kapanış (10) |
| **2. Yüz**<br>Çıktı: Noktalardan mesafeden bağımsız ölçüm üretmek ve ölçümün sınırını tanımak<br>Aşama: 4-6 | 0:00 Tekrar (10)<br>0:10 OpenCV ve MediaPipe'ın rolleri, Tasks API (15)<br>0:25 Yüz tespiti, kutu, noktalar, Haar karşılaştırması (25)<br>0:50 Takip ve tanıma farkı, hareket izi, EMA (25) | 1:30 Aynalama, koordinatlar, normalize ölçüm (20)<br>1:50 EAR, ağız açıklığı, baş yönelimi, blendshape (30)<br>2:20 Yüz oranları, sınırları, "Bir kamera neyi ölçebilir?" (20)<br>2:40 Mesafe ve poz deneyi (20) |
| **3. El**<br>Çıktı: Gürültülü model çıktısından güvenilir komut üretmek<br>Aşama: 7-8 | 0:00 Tekrar (10)<br>0:10 21 el noktası, eklem açıları, parmak durumları (25)<br>0:35 Sağ/sol etiketi ve aynalama deneyi (15)<br>0:50 Pinch ve normalize mesafe (25) | 1:30 Histerezis, bekleme ve soğuma süresi, el kaybında sıfırlama (30)<br>2:00 Sürgü, sürükleme ve çizim (35)<br>2:35 Tek komut testi ve eşik ayarı (25) |
| **4. Cilt ve birleşik uygulama**<br>Çıktı: Kaliteye bağlı, açıklanabilir ve sınırları belirtilmiş analiz yapmak<br>Aşama: 9-11 | 0:00 Tekrar (10)<br>0:10 Cilt bölgeleri, dışarıda bırakma, segmentasyon modeli (25)<br>0:35 Görüntü kalite kontrolü (20)<br>0:55 Görünüm göstergeleri ve ısı haritaları (20) | 1:30 Işığın etkisi deneyi (20)<br>1:50 Kural tabanlı analiz ve öğrenilmiş model; açık kaynak model değerlendirmesi (20)<br>2:10 Birleşik uygulama ve mimari (30)<br>2:40 Final demo ve sonraki adımlar (20) |

Zamanlar oturum başlangıcına göredir; parantez içindeki sayılar dakikadır. İkinci bölüm, 1:15-1:30
arasındaki aradan sonra başlar.

## Tek günlük 6 saatlik kısa sürüm

Kısa sürüm toplam **360 dakikadır**: **300 dakika** eğitim ve uygulama, **60 dakika** ara (15 + 30 + 15).
Kurulumun eğitimden önce hazırlık listesine göre tamamlanmış olması gerekir.

| Blok | Süre | İçerik | Uygulamalı | Yalnızca gösterim |
|---|---|---|---|---|
| 1 | 75 dk | Kamera, piksel, renk uzayları, ROI | 01, 02 | 03 (filtre, eşik, morfoloji, kontur) |
| Ara | 15 dk | | | |
| 2 | 80 dk | Yüz tespiti, noktalar, takip, EAR ve baş yönelimi | 04, 05, 06 (EAR ve poz) | Haar karşılaştırması, One Euro filtresi, yüz şekli eğilimi |
| Öğle arası | 30 dk | | | |
| 3 | 75 dk | El noktaları, pinch, histerezis, sürgü | 07, 08 (sürgü) | Çizim ve sürükleme, soğuma süresinin ayarı |
| Ara | 15 dk | | | |
| 4 | 70 dk | Cilt bölgeleri, kalite kontrolü, birleşik demo | 09, 10 | Segmentasyon modeli, ısı haritalarının ayrıntılı yorumu, açık kaynak model tartışması |

Kısa sürümde hiçbir cilt modeli sıfırdan eğitilmez. Seviye 2 yalnızca hazır bir segmentasyon modelinin
nasıl kullanıldığının gösterimi ve akne derecelendirme modelinin neden varsayılan olarak entegre
edilmediğinin tartışmasıyla sınırlı kalır; model eğitimi için gereken veri, süre ve donanım bu
eğitimin kapsamı dışındadır.

# B. Ön bilgiler ve gerekli araçlar

**Beklenen ön bilgi:** Değişken, liste, döngü, fonksiyon ve sınıf kullanımı düzeyinde Python. Görüntü
işleme veya makine öğrenmesi bilgisi gerekmez.

**Donanım ve sistem:** Dahili kamerası olan bir dizüstü bilgisayar; Windows 10/11 (x64) veya macOS 13
Ventura ve üstü. Ayrı ekran kartı gerekmez; bütün modeller işlemcide (CPU) çalışır. Kurulum yaklaşık
150 MB indirme ve 500 MB disk alanı gerektirir. İnternet yalnızca kurulum sırasında gerekir.

**Kullanılmayanlar:** Ücretli API, abonelik, kredi kartı, zorunlu bulut servisi, harici kamera,
Arduino, Raspberry Pi veya derinlik kamerası.

| Araç | Sürüm | Görevi |
|---|---|---|
| Python | 3.12 | Programlama dili |
| OpenCV (`opencv-contrib-python`) | 4.14.0.94 | Kamera, renk dönüşümü, filtreler, çizim |
| NumPy | 2.x | Görüntüyü sayı dizisi olarak işlemek |
| MediaPipe (Tasks API) | 1.1.1 | Yüz ve el için öğrenilmiş modeller |
| Pillow | 10 ve üstü | Ekrana Türkçe karakterli yazı |
| Kod düzenleyici | herhangi biri | Kodları okumak ve değiştirmek |

## Hazırlık kontrol listesi

Aşağıdaki adımlar eğitimden önce tamamlanır (ayrıntılar D bölümündedir; aynı liste
`docs/HAZIRLIK_KONTROL_LISTESI.md` dosyasında da bulunur):

1. Python 3.12 kurulu ve `python --version` (Windows'ta `py -3.12 --version`) 3.12 gösteriyor.
2. Proje klasörü indirildi ve klasörün içinde sanal ortam (`.venv`) oluşturuldu.
3. `pip install -r requirements.txt` hatasız tamamlandı (Intel Mac: `requirements-intel-mac.txt`).
4. `python scripts/download_models.py` üç model için "[tamam]" yazdı.
5. `python scripts/check_setup.py --kamera` sonunda "Ortam hazır" yazdı.
6. Kamera izni terminal veya kod düzenleyici için açık; Zoom, Teams gibi uygulamalar kapalı.
7. Kamera kullanmak istemeyen katılımcı için kendi çektiği bir video veya fotoğraf hazır (isteğe bağlı).
8. Bilgisayarın şarj aleti yanında.

# C. GitHub araştırması ve teknoloji seçimi

## Yöntem

Araştırma 19 Ekim 2026 tarihinde yapılmıştır. Adaylar yalnızca README açıklamalarıyla değil; kaynak
kodu, bağımlılık dosyaları, lisans dosyaları, model kartları, PyPI ve npm paket kayıtları ve GitHub
API'sinden alınan bakım bilgileriyle değerlendirilmiştir. Çekirdek bileşenler bu makinede (Apple M4,
macOS 27) üç ayrı ortamda kurulmuş ve proje testleri çalıştırılmıştır. Kod lisansı, model ağırlığı
lisansı ve veri kümesi lisansı ayrı ayrı ele alınmıştır: bir deponun herkese açık olması, kodun veya
ağırlıkların serbestçe kullanılabileceği anlamına gelmez.

İnceleme durumu kısaltmaları: **[Ç]** yerel olarak çalıştırıldı · **[K]** kaynak kodu incelendi ·
**[B]** yalnızca dokümantasyon üzerinden değerlendirildi · **[D]** erişim veya bağımlılık nedeniyle
doğrulanamadı.

Karşılaştırma tablosu (Tablo C1), on bir sütunu okunabilir kalsın diye raporun sonundaki ekte yatay
sayfada verilmiştir.


GitHub bakım bilgileri (19.10.2026, yıldız sayısı kalite ölçütü olarak kullanılmamıştır): OpenCV 91.226
yıldız, son gönderim 19.10.2026; MediaPipe 37.327 yıldız, 16.10.2026; mediapipe-samples 2.869 yıldız,
139 açık konu, 16.10.2026; opencv_zoo 1.093 yıldız, 28.05.2026; cvzone 1.335 yıldız, 52 açık konu,
10.05.2024; skin-scan 16 yıldız, 27.10.2025; VitalGaze 0 yıldız, 19.03.2026; acne-lds 3 yıldız,
30.04.2024.

## Araştırmanın önemli bulguları

1. **Eski MediaPipe arayüzü kaldırılmıştır.** `mediapipe` 1.1.1 paketinde `mp.solutions` ve
   `mediapipe.framework.formats` bulunmamaktadır (bu makinede denendi). İnternetteki örneklerin
   büyük kısmı, cvzone, skin-scan, VitalGaze ve hatta resmî Raspberry Pi örneği bu arayüzü kullandığı
   için güncel sürümle çalışmaz. Bu projede yalnızca Tasks API (`mp.tasks.vision`) kullanılır.
2. **Intel işlemcili Mac'ler ayrı bir yol gerektirir.** PyPI kayıtlarına göre MediaPipe 0.10.30
   (Aralık 2025) ve sonrası macOS için yalnızca Apple Silicon (arm64) paketi yayımlamaktadır. Intel Mac'lerde
   kurulabilen son sürüm 0.10.21'dir; bu sürüm `numpy<2` ister ve Python 3.9-3.12'yi destekler. Proje
   kodu iki sürümle de aynı şekilde çalışacak biçimde yazılmış ve iki sürümde de test edilmiştir.
3. **OpenCV paket çakışması.** MediaPipe kendi bağımlılığı olarak `opencv-contrib-python` kurar.
   Aynı ortama ayrıca `opencv-python` kurulursa iki paket aynı `cv2` klasörünü paylaştığı için hatalar
   oluşur. Bu nedenle `requirements.txt` yalnızca `opencv-contrib-python` içerir.
4. **Python sürümü.** Python 3.12, hem ana yapılandırmayı (MediaPipe 1.1.1: Python 3.9-3.14; NumPy 2.5:
   3.12 ve üstü) hem Intel Mac yapılandırmasını (MediaPipe 0.10.21: 3.9-3.12) destekleyen ortak sürümdür.
5. **OpenCV 4.14 ile 5.0.** Sürüm sabitlenmeden yapılan kurulumda pip, MediaPipe ile birlikte OpenCV 5.0'ı getirir. Bu
   eğitimde yaygın belgelerle uyumlu olgun 4.x hattından 4.14.0.94 sabitlenmiştir; kod OpenCV 5.0.0.93
   ile de test edilmiş ve aynı sonucu vermiştir.

## Bu eğitimin koşullarına en uygun seçenek

**Python + OpenCV + NumPy + MediaPipe Tasks API** seçilmiştir. Gerekçeler: ücretsiz ve açık lisanslı
kod (Apache-2.0) ile açık lisanslı model ağırlıkları (model kartlarına göre Apache-2.0); kurulumun
tek bir `pip` komutuyla tamamlanması; Windows x64 ve Apple Silicon için hazır paketler; modellerin
işlemcide gerçek zamanlı çalışması (bu makinede yüz ve el birlikte kare başına yaklaşık 12 ms);
ağırlıkların indirildikten sonra çevrimdışı çalışması; aynı modellerin tarayıcı sürümünün de
bulunması. OpenCV görüntünün "nasıl" işlendiğini, MediaPipe ise öğrenilmiş modelin "ne" bulduğunu
göstermek için kullanılır; böylece öğrenciler yalnızca hazır model çağırmaz.

## Cilt analizi depolarının değerlendirmesi

İncelenen cilt depolarından hiçbiri doğrudan entegrasyona uygun bulunmamıştır. skin-scan eğitici
fikirler içerir (LAB a* kanalı, parlak ve soluk piksellerle yansıma tespiti, Laplace ile doku), ancak
eski arayüzü kullanır, haritalarına web kamerasıyla doğrulanamayacak biyolojik adlar verir ve bölge
maskeleri göz ve ağzı da içerir. VitalGaze lisanssızdır, kaynağı belirsiz bir pickle modeli içerir ve
yüz renginden sarhoşluk çıkarımı yapmaya çalışır; bu yaklaşım bilimsel ve etik açıdan uygun değildir.
acne-lds hakemli bir çalışmaya dayanır ve kodu MIT lisanslıdır, ancak ağırlıkların lisansı
belirtilmemiş, eğitim verisi yalnızca akademik kullanıma açıktır ve model klinik fotoğraflarla
eğitilmiştir.

Bu nedenle cilt modülü iki seviyede tasarlanmıştır: OpenCV ile yazılmış, her adımı görülebilen bir
**Seviye 1** başlangıç modülü ve yalnızca "bu piksel yüz cildi mi?" sorusunu yanıtlayan, lisansı açık
bir segmentasyon modelinin entegre edildiği **Seviye 2** (ayrıntılar I bölümünde).

# D. Kurulum ve ilk kamera görüntüsü

**Öğrenme hedefi:** Projeyi kurmak, ortamın doğru çalıştığını kanıtlamak ve kamerayı açıp düzgün
kapatan ilk programı anlamak.

**Kavram:** Sanal ortam (`.venv`), projenin paketlerini bilgisayardaki diğer Python projelerinden
ayıran bir klasördür. Bir kamera, saniyede belirli sayıda kare veren bir kaynaktır; program her döngüde
bir kare okur, işler ve gösterir.

**Projede kullanıldığı yer:** Bütün örnekler aynı sanal ortamı ve aynı `models/` klasörünü kullanır.
Kamera okuma kodu `src/camera.py` içinde toplanmıştır.

## Windows (10/11, x64)

1. [python.org](https://www.python.org/downloads/) adresinden Python 3.12 için "Windows installer
   (64-bit)" indirilir; kurulumda **Add python.exe to PATH** işaretlenir. Kontrol: `py -3.12 --version`.
2. Proje klasörü indirilir ve komut istemi (cmd) bu klasörde açılır.
3. Sanal ortam oluşturulur ve etkinleştirilir:

   ```bash
   py -3.12 -m venv .venv
   .venv\Scripts\activate.bat
   ```

   PowerShell kullanılıyorsa etkinleştirme komutu `.venv\Scripts\Activate.ps1` olur. Betik çalıştırma
   engeli görülürse yalnızca o pencere için `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
   kullanılabilir; sistem ayarı değişmez.
4. Paketler ve modeller kurulur:

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   python scripts/download_models.py
   ```

5. Kamera izni: **Ayarlar > Gizlilik ve güvenlik > Kamera** bölümünde "Kamera erişimi" ve
   "Masaüstü uygulamalarının kameraya erişmesine izin ver" açık olmalıdır.
6. Kontrol: `python scripts/check_setup.py --kamera`

Windows on ARM (Snapdragon) bilgisayarlarda OpenCV'nin ARM paketi bulunmadığından x64 Python
kurulması gerekir; bu yapılandırma bu çalışmada denenmemiştir.

## macOS (13 Ventura ve üstü)

1. İşlemci türü öğrenilir: Terminal'de `uname -m` komutu `arm64` (Apple Silicon) veya `x86_64`
   (Intel) yazar.
2. Python 3.12, [python.org](https://www.python.org/downloads/macos/) yükleyicisiyle veya Homebrew
   ile (`brew install python@3.12`) kurulur. Kontrol: `python3.12 --version`.
3. Proje klasöründe sanal ortam oluşturulur, etkinleştirilir ve paketler kurulur:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   python scripts/download_models.py
   ```

   Intel Mac'te dördüncü satır `pip install -r requirements-intel-mac.txt` olarak çalıştırılır.
   Apple Silicon'da `python -c "import platform; print(platform.machine())"` komutu `arm64`
   yazmalıdır; `x86_64` yazıyorsa terminal Rosetta altında çalışıyordur.
4. Kamera izni: İlk çalıştırmada macOS izin sorar. İzin verilmediyse **Sistem Ayarları > Gizlilik ve
   Güvenlik > Kamera** bölümünde Terminal (veya VS Code, iTerm) açılır ve terminal yeniden başlatılır.
5. Kontrol: `python scripts/check_setup.py --kamera`

`download_models.py` modelleri MediaPipe'ın resmî deposundan, sürüm numaralı adreslerden indirir ve
her dosyayı SHA-256 özetiyle doğrular. Bozuk veya yarım kalmış dosya silinir ve yeniden indirilir.
Modeller toplam 28 MB'tır; indirildikten sonra internet gerekmez.

**Uygulama akışı (01_kamera.py):** kamera açılır → her döngüde kare okunur → kare aynalanır →
FPS hesaplanır → kare gösterilir → `q` tuşunda döngüden çıkılır → kamera serbest bırakılır.

```python
# examples/01_kamera.py (kısaltılmış) · Çalıştırma: python examples/01_kamera.py
cap = cv2.VideoCapture(source)
try:
    while True:
        ok, frame = cap.read()          # ok: başarılı mı, frame: NumPy dizisi
        if not ok:
            break
        frame = cv2.flip(frame, 1)      # ayna görüntüsü
        cv2.imshow("VISION LAB - 01 Kamera (q: cikis)", frame)
        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
            break
finally:
    cap.release()                       # kamera ışığı sönmeli
    cv2.destroyAllWindows()
```

`try/finally` yapısı, program bir hatayla dursa bile kameranın bırakılmasını sağlar. Projenin
diğer dosyalarında aynı görevi `with Camera(...) as cam:` yapısı üstlenir.

**Ekranda beklenen sonuç:** Ayna gibi çevrilmiş kamera görüntüsü ve üstte çözünürlük, kanal sayısı,
veri tipi (`uint8`) ve FPS bilgisi.

**Başarılı çalışma ölçütü:** `check_setup.py --kamera` "Ortam hazır" yazar; pencere açılır; `q` ile
kapanınca terminalde "Kamera serbest bırakıldı" görünür ve kamera ışığı söner.

**Tipik hata ve çözümü:** "Kamera açılamadı" mesajı çoğunlukla kameranın başka bir uygulamada açık
olmasından veya iznin verilmemesinden kaynaklanır. Uygulamalar kapatılır, izin açılır; harici bir
kamera takılıysa `--source 1` denenir.

**Küçük deney:** Program çalışırken bir video görüşmesi uygulaması kameraya erişmeye çalıştırılır ve
hangi programın kamerayı alabildiği gözlenir. Kameranın aynı anda tek bir uygulamaya ait olabildiği
görülür.

# E. Görüntü işleme temelleri

**Öğrenme hedefi:** Bir görüntünün sayılardan oluşan bir dizi olduğunu görmek ve kural tabanlı bir
işleme hattını (ROI → küçültme → bulanıklaştırma → eşik → morfoloji → kontur) kurmak.

**Kavramlar:**

- **NumPy dizisi:** Renkli bir kare `(yükseklik, genişlik, 3)` boyutunda bir dizidir. 1280×720 bir
  kare için `frame.shape` değeri `(720, 1280, 3)` olur. Veri tipi `uint8`dir; her değer 0-255
  arasındadır. `frame[y, x]` bir pikselin üç kanal değerini verir; önce satır (y), sonra sütun (x) yazılır.
- **BGR ve RGB:** OpenCV kanalları **mavi, yeşil, kırmızı** sırasıyla tutar; MediaPipe ve çoğu kütüphane
  RGB bekler. Dönüştürmeden verilen bir kare, ten renklerinin mavimsi görünmesine yol açar
  (02_piksel_renk.py içinde `b` tuşu bu hatayı gösterir).
- **Gri ton:** Üç kanal tek kanala indirilir: OpenCV yaklaşık `0,299 R + 0,587 G + 0,114 B` kullanır.
- **HSV:** Renk tonu (H), doygunluk (S) ve parlaklık (V). OpenCV'de H 0-179 aralığındadır. Renk
  tonunu parlaklıktan ayırdığı için renk seçimini kolaylaştırır.
- **LAB:** L açıklığı, a yeşil-kırmızı eksenini, b mavi-sarı eksenini taşır (CIE 1976 L\*a\*b\*).
  OpenCV'nin 8 bitlik kodlamasında `L = L* × 255/100`, `a = a* + 128`, `b = b* + 128` olur. Cilt
  bölümünde kullanılan "a\*" değeri bu kanaldır.
- **ROI (ilgi bölgesi):** Görüntünün bir parçasıdır ve NumPy dilimiyle alınır: `roi = frame[y1:y2, x1:x2]`.
  Kopya değil görünümdür; ROI üzerine çizim yapmak ana kareyi de değiştirir.
- **Yeniden boyutlandırma:** `cv2.resize`. Küçültmede `INTER_AREA`, büyütmede `INTER_LINEAR` daha temiz
  sonuç verir. Daha küçük kare, sonraki bütün adımları hızlandırır.
- **Gaussian bulanıklık:** Her pikseli komşularının ağırlıklı ortalamasıyla değiştirir; gürültüyü
  azaltır. Çekirdek boyutu tek sayı olmalıdır (3, 5, 7...).
- **Eşikleme:** Bir değerin altını siyah, üstünü beyaz yapar. Otsu yöntemi (Otsu, 1979) eşiği
  histogramdan otomatik seçer.
- **Morfolojik işlemler:** "Açma" küçük beyaz lekeleri siler, "kapama" küçük siyah delikleri kapatır.
- **Kontur:** Beyaz bölgelerin sınır eğrileridir; `cv2.findContours` ile bulunur, alanı ve çevresi ölçülebilir.
- **FPS ve gecikme:** FPS saniyede gösterilen kare sayısıdır. Gecikme, bir hareketin ekranda görünmesine
  kadar geçen süredir; işlem süresine kamera ve ekran tamponları eklenir. 30 FPS için kare başına
  bütçe yaklaşık 33 ms'dir.
- **Kural tabanlı yöntem ve öğrenilmiş model:** Kural tabanlı yöntemde her adımı insan yazar ("bu
  eşiğin altı siyahtır"); davranış açıklanabilir ama koşullar değişince bozulabilir. Öğrenilmiş model
  kuralları örneklerden çıkarır; karmaşık örüntüleri yakalar ama neden o sonucu verdiği doğrudan
  görülemez ve eğitim verisinin dışındaki koşullarda yanılabilir.

**Projede kullanıldığı yer:** Bütün modüller BGR→RGB dönüşümünü `src/common/frame.py` içinde bir kez
yapar. Cilt modülü LAB uzayını, kalite kontrolü Laplace işlemini, bölge maskeleri morfolojik aşındırma
ve genişletmeyi kullanır.

**Uygulama akışı (03_filtre_esik.py):** kare küçültülür → fareyle ROI seçilir → gri tona çevrilir →
Gaussian bulanıklık → sabit veya Otsu eşiği → açma ve kapama → konturlar bulunur ve sayılır → her
adımın süresi milisaniye olarak gösterilir.

```python
# examples/03_filtre_esik.py (kısaltılmış) · Çalıştırma: python examples/03_filtre_esik.py
region = small[y1:y2, x1:x2]                                  # ROI
gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (k, k), 0)
used, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (m, m))
cleaned = cv2.morphologyEx(cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel), cv2.MORPH_CLOSE, kernel)
contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```

**Ekranda beklenen sonuç:** Dört kutucuk: konturları çizilmiş orijinal görüntü, bulanık gri görüntü,
eşiklenmiş ikili görüntü ve temizlenmiş görüntü; altta adım süreleri ve FPS. 02 numaralı örnekte ise
orijinal, gri, H, V, L ve a kanalları yan yana görünür ve tıklanan pikselin değerleri terminale yazılır.

**Başarılı çalışma ölçütü:** Tıklanan pikselin BGR, RGB, HSV ve LAB değerleri tutarlıdır; sürgüler
değiştikçe eşik ve kontur sayısı değişir; adım süreleri görünür.

**Tipik hata ve çözümü:** `cv2.GaussianBlur` çift sayılı çekirdekle hata verir; örnek kod sürgü
değerini `2n+1` ile tek sayıya çevirir. `cv2.putText` ile yazılan Türkçe karakterler "?" görünür;
projedeki `put_text` yardımcı fonksiyonu sistem yazı tipini Pillow ile kullanır.

**Küçük deney:** Oda ışığı kısılıp açıldığında sabit eşik ile Otsu eşiğinin kontur sayısı karşılaştırılır.
Sabit kuralın ışık değişimine ne kadar duyarlı olduğu, öğrenilmiş modellere neden ihtiyaç duyulduğunu
gösterir.

# F. Yüz tespiti ve takibi

**Öğrenme hedefi:** Öğrenilmiş bir modelle yüzü bulmak, 478 noktayı çizmek, yüzü kareler boyunca
izlemek ve titremeyi azaltmak.

**Kavramlar:**

- **Tespit:** "Bu karede yüz var mı, nerede?" sorusudur. Sonuç bir kutu veya noktalardır.
- **Takip:** "Önceki karedeki yüz bu karede hangisi?" sorusudur. Bu projede her yüze bir **iz
  numarası** verilir. Bu numara kişinin kimliği değildir; yüz kadrajdan çıkıp girdiğinde yeni numara
  alabilir.
- **Tanıma:** "Bu kişi kim?" sorusudur. Kimlik tanıma bu eğitimin parçası değildir; kullanılan
  MediaPipe model kartları gözetim ve kimlik tanımayı açıkça kapsam dışı sayar.
- **MediaPipe Face Landmarker:** Önce BlazeFace dedektörü yüzü bulur (Bazarevsky vd., 2019), ardından
  Face Mesh V2 modeli 256×256'ya ölçeklenen yüz kesitinde 478 nokta üretir (model kartı; Kartynnik vd.,
  2019). VIDEO modunda model önceki karedeki konumu kullanır ve her karede yeniden tespit yapmaz.
- **Hareket izi ve yumuşatma:** Yüz merkezi her karede kaydedilir. Üstel hareketli ortalama (EMA)
  `yeni = α · ölçüm + (1 − α) · eski` formülüyle titremeyi azaltır; α küçüldükçe iz yumuşar ama
  gecikir. Hıza göre kendini ayarlayan One Euro filtresi (Casiez vd., 2012) ileri seçenek olarak
  `src/common/smoothing.py` içinde bulunur.
- **Klasik yöntemle karşılaştırma:** OpenCV'nin Haar sınıflandırıcısı (Viola ve Jones, 2001) da
  öğrenilmiş bir yöntemdir ancak yalnızca kutu verir ve yan pozlarda zayıftır.

**Projede kullanıldığı yer:** `src/face/tracker.py` modeli bir kez yükler (`FaceTracker`), her karede
`process(frame)` ile çalıştırır ve yüzleri en yakın merkez eşleştirmesiyle izlere bağlar.

**Uygulama akışı:** kare hazırlanır (küçültme, RGB, `mp.Image`) → `detect_for_video(görüntü,
zaman_damgası)` → normalize noktalar piksele çevrilir → kutu ve merkez hesaplanır → iz numarası atanır →
EMA ile merkez yumuşatılır → çizim yapılır → yüz yoksa durum mesajı gösterilir.

```python
# src/face/tracker.py (kısaltılmış)
options = vision.FaceLandmarkerOptions(
    base_options=base_options(config.FACE_MODEL),
    running_mode=vision.RunningMode.VIDEO,    # kareler sırayla verilir, takip açık
    num_faces=1, output_facial_transformation_matrixes=True)
self._landmarker = vision.FaceLandmarker.create_from_options(options)   # bir kez
...
result = self._landmarker.detect_for_video(frame.mp_image, frame.timestamp_ms)
points = to_pixels(result.face_landmarks[0], width, height)              # (478, 2)
```

VIDEO modunda zaman damgaları her karede artmalıdır; `src/common/frame.py` içindeki `FrameClock`
aynı milisaniyede gelen iki kareye bile farklı değer verir.

## Koordinatlar, aynalama ve derinlik

MediaPipe noktaları 0-1 aralığında **normalize** verir: `x` görüntü genişliğine, `y` yüksekliğine
bölünmüştür. Genişlik ve yükseklik farklı olduğundan iki nokta arasındaki mesafe ancak piksele
çevrildikten sonra ölçülmelidir (`src/common/geometry.py`). Görüntü koordinatlarında `y` aşağı doğru artar.

Kullanıcıya ayna görüntüsü doğal gelir, ancak bu projede **model her zaman aynalanmamış kareyi görür**
ve ayna yalnızca ekrana uygulanır. Böylece "sol göz" veya `eyeBlinkLeft` gibi çıktılar kişinin gerçek
sol tarafını gösterir; MediaPipe belgeleri de blendshape adlarındaki sol/sağın kişinin yüzüne göre
olduğunu ve aynalanmış girdinin bunları ters çevireceğini belirtir. Çizim sırası bu yüzden önemlidir:
önce şekiller aynalanmamış görüntüye çizilir, sonra görüntü aynalanır, en son yazılar eklenir
(`src/common/app.py`, `Canvas`). Bu projede ölçülen bir örnek: aynı fotoğraf yatayda çevrildiğinde
baş dönüş açısının işareti +4,9°'den −5,2°'ye değişmiş, eğim açısı aynı kalmıştır.

Yüz noktalarının `z` değeri santimetre değildir. Face Mesh V2 model kartına göre `z`, yüzün kütle
merkezine görelidir ve yüz genişliğiyle orantılı ölçeklenir. Tek bir kamera gerçek derinliği
ölçmez; `z` yalnızca noktaların birbirine göre önde veya arkada olduğunu gösterir.

**Ekranda beklenen sonuç:** 04 numaralı örnekte yüz çevresinde mavi kutu, göz, kaş, dudak ve yüz
çevresi konturları, kutunun üstünde "iz 1" ve altta durum satırı. 05 numaralı örnekte gri ince bir ham
iz ile turkuaz kalın bir yumuşatılmış iz görünür.

**Başarılı çalışma ölçütü:** Yüz noktaları baş hareketini gecikmeden izler; yüz kadrajdan çıkınca
"Yüz bulunamadı" mesajı görünür ve iz birkaç kare sonra silinir; `+` ve `-` tuşlarıyla α değiştikçe
iz belirgin biçimde yumuşar veya titrekleşir.

**Tipik hata ve çözümü:** `ValueError: Input timestamp must be monotonically increasing` hatası, VIDEO
modunda aynı veya geriye giden zaman damgası verildiğini gösterir; `FrameClock` kullanılır. Birden
fazla yüz için `--max-faces 2` verilebilir; MediaPipe belgelerine göre kendi yumuşatması yalnızca
tek yüz modunda uygulanır.

**Küçük deney:** α = 0,10 ve α = 0,80 ile baş hızlıca sağa sola hareket ettirilir. Hangi değerin daha
titrek, hangisinin daha gecikmeli olduğu not edilir.

# G. Yüz geometrisi ve hareket analizi

**Öğrenme hedefi:** Noktalardan mesafeden bağımsız ölçümler üretmek ve bu ölçümlerin sınırlarını
tanımak.

**Kavramlar:**

- **Normalize mesafe:** Bir uzunluğu başka bir yüz uzunluğuna bölmek, kişi kameraya yaklaşınca
  değişmeyen bir oran verir. Projenin testlerinde standart yüz modeli üç farklı ölçekte yansıtılmış ve
  oranlar on binde bir hassasiyetle aynı çıkmıştır.
- **Göz en-boy oranı (EAR):** `(|p2−p6| + |p3−p5|) / (2·|p1−p4|)`; göz kapandıkça 0'a yaklaşır
  (Soukupová ve Čech, 2016). Sabit 0,20 eşiği önerilir; ancak örnek görüntülerde açık gözde 0,20-0,32
  ölçülmüş, gülümseyen bir yüzde 0,20 değeri görülmüştür. Bu nedenle `BlinkDetector` kişinin son
  karelerdeki ortancasını temel alır ve gözü bu değerin %65'inin altına inince kapalı sayar.
- **Ağız açıklığı:** İç dudak mesafesinin ağız genişliğine oranı.
- **Yaklaşık baş yönelimi:** Face Landmarker'ın 4×4 dönüşüm matrisinden dönüş (yaw), eğim (pitch) ve
  yatma (roll) açıları hesaplanır. Fotoğraf 15° döndürüldüğünde yatma açısının yaklaşık 15° değiştiği
  bu projede ölçülmüştür. Değerler yaklaşıktır ve kişiden kişiye birkaç derecelik sapma gösterebilir.
- **Kural tabanlı ve öğrenilmiş ölçüm:** Aynı ekranda EAR (geometri) ile modelin `eyeBlinkLeft` gibi
  blendshape katsayıları (0-1) yan yana gösterilir. Blendshape katsayısı bir olasılık değil, modelin
  ürettiği ifade katsayısıdır.
- **Yüz oranları:** uzunluk/genişlik (nokta 10 ile 152 arası / 234 ile 454 arası), çene/elmacık ve
  üst alın/elmacık oranları.

**Projede kullanıldığı yer:** `src/face/metrics.py`; poz kontrolü cilt modülünün kalite kontrolünde
de kullanılır.

**Uygulama akışı (06_yuz_geometrisi.py):** noktalar → EAR, ağız oranı, poz, oranlar → önden poz,
yüz boyutu ve kararlılık kontrolü → koşullar uygunsa yaklaşık şekil eğilimi, değilse "Uygun görüntü
bekleniyor" ve nedeni.

```python
# examples/06_yuz_geometrisi.py (kısaltılmış) · Çalıştırma: python examples/06_yuz_geometrisi.py
if not is_frontal(face.pose):
    return "Uygun görüntü bekleniyor: başınızı düz tutup kameraya bakın."
ratios = face_ratios(face.points)
history.append(ratios["uzunluk/genişlik"])
if len(history) < config.SHAPE_STABLE_FRAMES or np.std(history) > config.SHAPE_MAX_RATIO_STD:
    return "Uygun görüntü bekleniyor: birkaç saniye hareketsiz kalın."
return f"Yaklaşık: {approximate_shape_tendency(ratios)} (standart bir sınıf değildir)"
```

## Yüz şekli etiketlerinin sınırları

Oval, yuvarlak veya kare gibi etiketler standart ve kesin sınıflar değildir; bu projede yalnızca
"eğilim" olarak ve uygun koşullarda gösterilir. Sınırlar, MediaPipe'ın ortalama yüz modelinin önden
bakıştaki değerlerinin (uzunluk/genişlik 1,29; çene/elmacık 0,80) çevresine konmuş deneysel değerlerdir.
Etkileyen başlıca etkenler şunlardır:

- **Alın sınırı:** Yüz ağının en üst noktası saç çizgisi değil alnın ortasıdır; saç alnı örterse gerçek
  yüz uzunluğu zaten görülemez.
- **Poz ve perspektif:** Standart yüz modeli döndürülerek yapılan ölçümde, 30° baş dönüşünde
  uzunluk/genişlik oranı 1,29'dan 1,45'e (%12) çıkmıştır (Şekil G1). Bu yüzden etiket yalnızca önden
  pozda üretilir.
- **Kamera mesafesi ve lens:** Çok yakın çekimde geniş açılı dizüstü kameraları burun ve yanakları
  büyütür.

![**Şekil G1.** Baş dönüşü arttıkça uzunluk/genişlik oranı (standart yüz modeli üzerinde hesaplanmıştır).](assets/sekil_poz_oran.png){width=72%}

## Bir kamera neyi ölçebilir?

Kamera ışığın piksellere düşen yoğunluğunu kaydeder. Buradan **gözlenebilir** büyüklükler çıkarılabilir:
noktaların konumu, oranlar, göz kırpma, ağız açıklığı, baş yönelimi, hareketin hızı. Bunlar
**psikolojik yorum** değildir. Bir gülümseme sinyali (ör. `mouthSmileLeft`), ağız köşelerinin hareket
ettiğini gösterir; kişinin içsel olarak mutlu olduğunun kesin kanıtı değildir. Yüz hareketlerinden
duygu çıkarmanın kültüre, bağlama ve kişiye göre güvenilmez olduğu kapsamlı bir derlemede gösterilmiştir
(Barrett vd., 2019). Bu projede kişilik, zekâ, güvenilirlik veya karakter çıkarımı yapılmaz; yüz
oranlarından böyle bir sonuç çıkarılamaz.

**Ekranda beklenen sonuç:** Sağ panelde EAR ve "açık/kapalı", göz kırpma sayısı, ağız oranı,
blendshape değerleri, üç açı ve üç oran; alt satırda şekil eğilimi veya bekleme nedeni.

**Başarılı çalışma ölçütü:** Kameraya yaklaşıp uzaklaşınca oranlar yaklaşık sabit kalır; göz
kırpınca sayaç bir artar; baş döndürülünce etiket yerine "Uygun görüntü bekleniyor" görünür.

**Tipik hata ve çözümü:** Gözlükteki yansımalar EAR değerini bozabilir; gözlük hafifçe eğilerek
yansıma azaltılır. Göz kırpma hiç algılanmıyorsa `config.EYE_CLOSED_RATIO` artırılır.

**Küçük deney:** Kameraya 40 cm ve 80 cm uzaklıktan bakılarak uzunluk/genişlik oranı not edilir; ardından
baş 20° döndürülerek aynı oran okunur. Mesafenin değil pozun oranı değiştirdiği görülür.

# H. El takibi ve jest analizi

**Öğrenme hedefi:** 21 el noktasından parmak durumlarını ve pinch hareketini belirlemek; gürültülü
model çıktısından tek ve güvenilir komut üretmek.

**Kavramlar:**

- **21 nokta:** 0 bilek; başparmak 1-4; işaret 5-8; orta 9-12; yüzük 13-16; serçe 17-20. Uç
  noktaları 4, 8, 12, 16, 20'dir. Hand Landmarker bir avuç dedektörü ve bir nokta modelinden oluşur
  (Zhang vd., 2020; model kartı).
- **Eklem açısı:** Bir parmağın açık mı kapalı mı olduğu orta eklemdeki (PIP) açıyla belirlenir; düz
  parmakta açı 180°'ye yaklaşır. "Uç, eklemin üstünde mi?" kuralı el döndüğünde bozulur; açı ise elin
  yönünden bağımsızdır. Örnek görüntülerde açık parmaklarda 163-180°, kapalı parmaklarda 5-80°
  ölçülmüştür.
- **Statik jestler:** Açık el (dört parmak açık), yumruk, işaret parmağı, V işareti ve başparmak yukarı.
- **Pinch ve normalize uzaklık:** Başparmak ucu ile işaret ucu arasındaki mesafe, avuç boyuna (bilek ile
  orta parmak kökü arası) bölünür; böylece el kameraya yaklaşınca değer değişmez.
- **Histerezis:** Pinch 0,25'in altında başlar, 0,40'ın üstünde biter. Tek eşikte, değer eşik
  çevresinde titredikçe durum defalarca değişir (Şekil H1).
- **Bekleme süresi (debounce):** Yeni durum 120 ms boyunca değişmeden kalmadıkça kabul edilmez.
- **Soğuma süresi (cooldown):** Bir komuttan sonra 700 ms boyunca yeni jest komutu üretilmez.
- **Kenar tetikleme:** Komut, pinch **başladığı anda** bir kez üretilir; parmaklar birleşik tutuldukça
  tekrar edilmez.
- **El kaybında sıfırlama:** El 300 ms görünmezse bütün durum sıfırlanır; böylece el geri geldiğinde
  eski bir "basılı tutma" devam etmez.
- **Sağ ve sol el:** Etiket modelin tahminidir. Eski örneklerin çoğu kareyi modele vermeden önce aynalar;
  bu, etiketin anlamını değiştirebilir. Bu projede model aynalanmamış kareyi görür ve etiketin doğruluğu
  07 numaralı örnekteki deneyle kontrol edilir; ters ise `config.HANDEDNESS_SWAP = True` yapılır.
  Jestler etikete bağlı değildir.

![**Şekil H1.** Eşik çevresinde kararsız kalan sentetik bir pinch sinyali: tek eşik 9, histerezis 1 komut üretir.](assets/sekil_histerezis.png){width=82%}

**Projede kullanıldığı yer:** `src/hands/gestures.py` (`GestureController`), `src/hands/widgets.py`
(sürgü, düğme çubuğu, sürüklenen kutu, çizim alanı). Birleşik uygulamada modlar arasında el ile geçiş
yapılır. İşletim sisteminin faresi kontrol edilmez.

**Uygulama akışı (08_el_jestleri.py):** el noktaları → işaret ucu ekran koordinatına çevrilir →
pinch oranı → histerezis → bekleme → olaylar (`pinch_basladi`, `pinch_bitti`, `jest:...`, `el_kayboldu`)
→ sürgü ve kutu yalnızca pinch başladığında tutulur → işaret jestinde çizim yapılır → açık el 1 saniye
tutulunca çizim silinir.

```python
# src/hands/gestures.py (kısaltılmış)
raw_pinch = self.pinch.update(pinch_ratio(points))          # histerezis
stable_pinch = self.pinch_debounce.update(raw_pinch, t_ms)  # bekleme süresi
if stable_pinch and not self.state.pinching:
    events.append("pinch_basladi")                          # yalnızca geçiş anında
gesture = self.gesture_debounce.update(classify_static(finger_states(points)), t_ms)
if gesture != previous and t_ms - self._last_command_ms >= config.COMMAND_COOLDOWN_MS:
    events.append(f"jest:{gesture}")                        # soğuma süresiyle sınırlı
```

**Ekranda beklenen sonuç:** Elin iskeleti, pinch sırasında başparmak ile işaret ucu arasında turuncu
bir çizgi, sağ üstte giriş ve çıkış eşikleri işaretli pinch çubuğu, solda kararlı ve ham jest adı ile
olay günlüğü, altta pinch ile sürüklenen sürgü.

**Başarılı çalışma ölçütü:** Bir pinch hareketi komut sayacını yalnızca bir artırır; parmaklar birleşik
tutuldukça sayaç artmaz; el kadrajdan çıkınca "El kayboldu: durum sıfırlandı" görünür ve sürgü bırakılır.
Bu davranışlar `tests/test_gestures.py` içinde gürültülü sentetik el verisiyle test edilmektedir.

**Tipik hata ve çözümü:** Pinch hiç başlamıyorsa el kameraya çok yandan bakıyordur veya eşik küçüktür;
pinch çubuğunda değer okunur ve `PINCH_ENTER_RATIO` ayarlanır. Yumruk "belirsiz" görünüyorsa
`FINGER_FOLDED_DEG` artırılır.

**Küçük deney:** `GESTURE_STABLE_MS` 0 yapılıp pinch sınırında el yavaşça açılıp kapatılır ve komut
sayısı not edilir; ardından 120 ms'ye dönülerek aynı deney tekrarlanır.

# I. Cilt görünümü analizi

**Öğrenme hedefi:** Yüzün belirli bölgelerinden, kalite kontrolünden geçmiş tek bir kare üzerinde
açıklanabilir görünüm göstergeleri üretmek ve bu göstergelerin neyi ölçmediğini bilmek.

::: {.uyari}
Eğitim amaçlı görüntü analizi; tıbbi tanı değildir. Bu modül nem, kolajen, vitamin, biyolojik yaş
veya genel cilt sağlığı yüzdesi üretmez. Normal bir web kamerasıyla bu büyüklükler doğrulanamaz.
:::

## Seviye 1: Açıklanabilir görüntü işleme

![**Şekil I1.** Standart yüz modeli üzerinde analiz bölgeleri. Koyu alanlar dışarıda bırakılır.](assets/sekil_bolgeler.png){width=44%}

**Kavramlar ve adımlar:**

1. **Bölgeler:** Alın ve iki yanak, yüz noktalarından çizilen çokgenlerle seçilir. Bölge adları kişinin
   kendi sağına ve soluna göredir (Şekil I1).
2. **Dışarıda bırakma:** Göz, kaş ve dudak çevresi kenar payıyla çıkarılır; bölgeler kenarlardan içeri
   çekilir (aşındırma), çünkü noktalar birkaç piksel kayabilir. Saç alnı örterse segmentasyon modeli
   (Seviye 2) veya yüz ortancasından çok koyu pikselleri atan renk tutarlılığı yöntemi kullanılır.
3. **Ölçek:** Yüz, genişliği 320 piksel olacak şekilde ölçeklenir; doku ölçümü mesafeden daha az etkilenir.
4. **Kalite kontrolü:** Tek yüz; yüz genişliği en az 180 piksel; baş pozu (dönüş ≤ 12°, eğim ≤ 20°,
   yatma ≤ 10°); göreli netlik (Laplace varyansı / gri ton varyansı × 1000 ≥ 20; Pech-Pacheco vd., 2000);
   pozlama (bölge parlaklık ortancası 50-235, doymuş piksel ≤ %8, çok karanlık piksel ≤ %10); en az iki
   bölgenin yarıdan fazlasının görünmesi. Biri başarısızsa **sonuç üretilmez**; "Uygun görüntü
   bekleniyor" ve nedeni gösterilir.
5. **Göstergeler:**

| Gösterge | Hesaplama | Ne değildir |
|---|---|---|
| Göreli kızarıklık görünümü (Δa\*) | Bölgenin a\* ortalaması − yüzün a\* ortancası | Klinik bir teşhis değildir |
| Parlak piksel oranı | Yüz ortancasından en az 25 düzey açık ve renk doygunluğu ortancanın %70'inden az piksellerin yüzdesi | Yağ üretiminin doğrudan ölçümü değildir |
| Doku değişimi | Büyük ölçekli aydınlatma çıkarıldıktan sonra kalan ince parlaklık dalgalanmasının yerel enerjisi | Gözenek veya hastalık tanısı değildir |
| Yerel renk farkı (ΔE76) | Her pikselin kendi bölgesinin ortanca rengine CIELAB uzaklığı | Leke tespiti değildir |
| İki yanak arası ΔE | İki yanağın ortanca renkleri arasındaki uzaklık | Asimetri tanısı değildir; çoğunlukla ışığın yönünden kaynaklanır |

6. **Isı haritaları:** Her gösterge yalnızca bölge maskesi içinde, **sabit bir aralıkla** renklendirilir
   (ör. Δa\* için −10 ile +10). Her görüntüyü kendi en düşük ve en yüksek değerine göre ölçeklemek
   küçük farkları büyük gösterir.

**Neden mutlak değil göreli?** İlk denemede "parlama" için mutlak bir eşik (L > 225) kullanılmış ve açık
tenli bir kişinin parlak stüdyo ışığındaki fotoğrafında bölgelerin %74-86'sı "parlak" sayılmıştır.
Yansıyan ışık cildin değil ışığın rengini taşıdığı için yüzün geri kalanına göre daha açık ve daha
soluk görünür; göreli ölçüt bu durumda %0 vermiştir. Netlik ölçüsü de benzer biçimde gri ton varyansına
bölünmüştür: ham Laplace varyansı karartılmış bir fotoğrafta 169'dan 12'ye düşerken (bulanık sanılır),
göreli ölçü 62'den 73'e değişmiştir. Göreli netlik ölçüsünün de bir sınırı vardır: görüntü gürültüsü
kenar gibi görünür ve değeri yükseltir.

**Sonuçları etkileyen etkenler:** Işığın rengi ve yönü, kameranın otomatik beyaz dengesi ve pozlaması,
kameranın görüntüyü keskinleştirme ve gürültü azaltma işlemleri, makyaj, sakal ve kıllar, gözlük ve
cilt tonu. Bu projede bir fotoğrafın renkleri sentetik olarak "sıcak ışık" yönünde kaydırıldığında
alnın mutlak a\* değeri 15,7'den 24,2'ye çıkmış, göreli değerler de birkaç birim değişmiştir; görüntünün
yarısı karartılarak yan ışık taklit edildiğinde iki yanak arası ΔE 3,1'den 27,2'ye yükselmiştir. Cilt
değişmemiştir; değişen ışıktır. Bu nedenle **farklı günlerde, standart ışık ve kamera ayarları olmadan
alınan ölçümler gerçek bir değişim gibi karşılaştırılmaz.** Pozlama alt sınırı, koyu cilt tonlarında
normal ışıkta da düşük parlaklık ölçülebileceği için bilerek düşük tutulmuştur; bu tür eşiklerin farklı
cilt tonlarında adil davranıp davranmadığı K bölümündeki test senaryolarıyla denetlenir (Buolamwini ve
Gebru, 2018).

**Projede kullanıldığı yer:** `src/skin/regions.py`, `quality.py`, `metrics.py`, `analyzer.py`. Analiz yüz
ve el takibi kadar sık çalışmaz: boşluk tuşuyla tek kare alınır veya `--otomatik` seçeneğinde kalite uygun
olduğunda iki saniyede bir çalışır. Kalite önizlemesi saniyede iki kez güncellenir.

```python
# src/skin/analyzer.py (kısaltılmış)
seg = self.segmenter.segment(crop) if self.segmenter is not None else None
regions = build_region_masks(crop, points, config.SKIN_ANALYSIS_FACE_WIDTH,
                             config.SKIN_ROI_EROSION_RATIO, seg)
quality = check_quality(crop, len(faces), width_full, face.pose, face_box, union, regions.coverage)
if not quality.ok:
    return SkinReport(quality, None, crop, regions)        # sonuç üretilmez
metrics = compute_metrics(crop, valid_regions)
```

**Ekranda beklenen sonuç (10_cilt_analizi.py):** Üstte her zaman görünen uyarı satırı, solda renkli
noktalarla kalite kontrol listesi, sağ panelde bölge maskesi içinde ısı haritası, sabit aralıklı renk
çubuğu, bölge tablosu ve iki yanak arası ΔE.

**Başarılı çalışma ölçütü:** Baş döndürüldüğünde, oda karartıldığında veya iki kişi kadrajdayken sonuç
üretilmez ve neden yazılır. Uygun koşulda boşluk tuşu bir analiz üretir ve görüntü kaydedilmez.

**Tipik hata ve çözümü:** "Bölge kapsaması" başarısızsa saç alnı örtüyordur veya gözlük yanaklara
gölge düşürüyordur; saç geriye alınır. "Netlik" başarısızsa kamera merceği silinir ve hareketsiz durulur.

**Küçük deney:** Aynı kişi önce pencereye dönük, sonra pencereye yan dönük iki analiz alır. Δa\* ve iki
yanak arası ΔE karşılaştırılır; cilt aynıyken değerlerin ışıkla değiştiği gözlenir.

## Seviye 2: Açık kaynak model entegrasyonu

**Entegre edilen model: MediaPipe Selfie Multiclass Segmenter (256×256).**

| Özellik | Değer |
|---|---|
| Görev | Segmentasyon: her piksele sınıf atar (arka plan, saç, vücut cildi, yüz cildi, giysi, diğer/aksesuar) |
| Girdi ve ön işleme | RGB görüntü; model 256×256'ya kendisi ölçekler; en-boy oranı serbest (model kartı) |
| Model dosyası | `selfie_multiclass_256x256.tflite`, 16,4 MB, MediaPipe resmî deposu, sürüm 1, SHA-256 doğrulamalı |
| Ağırlık ve veri lisansı | Model kartı: Apache-2.0. Eğitim verisi yayımlanmamış; kartta "çok sayıda farklı kimlikten binlerce örnek" ifadesi var |
| Değerlendirme | Kart: 918 görüntü, 1.902 kişi; Monk ölçeğinde 10 cilt tonu ve algılanan cinsiyete göre adalet değerlendirmesi |
| CPU maliyeti | Bu makinede (Apple M4) tam portrede ~33 ms; segmentasyon dahil cilt analizinin tamamı ortanca 37 ms |
| Kamera ile eğitim verisi farkı | Selfie ve video konferans için tasarlanmış; web kamerası kullanımına yakın |
| Bilinen sınırlamalar | Piksel düzeyinde kusursuz maske vermez; düşük ışık, arka ışık, gürültü ve büyük örtülmelerde bozulur; gözetim ve kimlik tanıma kapsam dışı |
| Entegrasyon | `src/skin/segmenter.py`; dosya yoksa cilt modülü renk tutarlılığı yöntemiyle çalışmaya devam eder |

Bu model cildin durumu hakkında hiçbir şey söylemez; yalnızca hangi piksellerin yüz cildi olduğunu
belirleyerek Seviye 1 göstergelerinin saçtan ve aksesuarlardan etkilenmesini azaltır. Örnek portrelerde
saç ve yüz cildi doğru ayrılmıştır.

**Değerlendirilen ancak entegre edilmeyen model: acne-lds.**

| Özellik | Değer |
|---|---|
| Görev | Görüntü sınıflandırma: Hayashi ölçeğinde 4 dereceli akne şiddeti ve 65 kutulu lezyon sayısı dağılımı |
| Girdi | 224×224, veri kümesine özgü ortalama ve standart sapma ile normalize RGB |
| Model dosyası | Google Drive klasörü (bağlantıyla görüntülenebiliyor); bu çalışmada indirilmedi |
| Ağırlık ve veri lisansı | Kod MIT; ağırlık lisansı belirtilmemiş; ACNE04 veri kümesi "yalnızca akademik kullanım" |
| Eğitim verisi kapsamı | ACNE04: akne değerlendirmesi için toplanmış yüz fotoğrafları |
| CPU maliyeti | ResNet-50; 224 piksel girdide yaklaşık 4,1 GFLOP (torchvision belgesi); ölçülmedi |
| Bağımlılık | `torch==1.10.1` sabitlenmiş; güncel Python sürümleriyle doğrudan kurulamaz |
| Neden entegre edilmedi | Ağırlık lisansı belirsiz; klinik fotoğraflardan web kamerasına alan farkı; çıktısı tıbbi derecelendirme anlamı taşıdığı için sınıf ortamında öğrencilerin yüzlerinde çalıştırılması uygun değil |

İleri aşamada bu model, öğrencilerin kendi yüzleri yerine lisans koşulları uygun bir veri kümesindeki
görüntülerle, ayrı bir sanal ortamda ve yalnızca model davranışını incelemek amacıyla denenebilir.
Bu entegrasyon bu projede uygulanmamış ve doğrulanmamıştır.

**Sınıflandırma, tespit ve segmentasyon farkı:** Sınıflandırma bütün görüntüye tek bir etiket verir
("2. derece"); tespit nesnelerin yerini kutularla gösterir; segmentasyon her piksele sınıf verir. acne-lds
bir sınıflandırıcıdır; bu yüzden ekranda lezyon kutusu çizmek modelin üretmediği bir bilgiyi uydurmak
olur. Grad-CAM gibi açıklama haritaları (Selvaraju vd., 2017) modelin kararında etkili olan bölgeleri
kabaca gösterir; gerçek lezyon segmentasyonu değildir.

# J. Modüllerin birleştirilmesi

```text
vision-workshop/
  README.md                  kurulum ve başlatma
  requirements*.txt          çekirdek, Intel Mac ve test bağımlılıkları
  workshop.config.json       organizasyon bilgileri (tek ayar yeri)
  models/                    indirilen model dosyaları
  scripts/                   model indirme, kurulum kontrolü, süre ölçümü
  src/
    main.py                  birleşik uygulama
    camera.py                kamera, video veya fotoğraf kaynağı
    config.py                bütün eşikler ve kaynakları
    common/                  kare hazırlama, çizim, FPS, geometri, yumuşatma
    face/                    yüz takibi, ölçümler, çizim
    hands/                   el takibi, jestler, arayüz öğeleri
    skin/                    bölgeler, kalite, göstergeler, segmentasyon
  examples/                  aşama aşama 10 örnek
  tests/                     kamera gerektirmeyen testler
  shared/                    sunumla paylaşılan standart yüz modeli
  docs/                      rapor, eğitmen notları, lisanslar, doğrulama
  presentation/              React + TypeScript + Vite web sunumu
```

| Modül | Girdi | Çıktı | Sorumluluk |
|---|---|---|---|
| `camera.py` | kamera numarası veya dosya | BGR kare | Kaynağı açmak, okumak, serbest bırakmak |
| `common/frame.py` | BGR kare | `Frame` (küçük kare, RGB, `mp.Image`, zaman damgası) | Kareyi bir kez hazırlamak |
| `face/tracker.py` | `Frame` | 478 nokta, kutu, iz, poz | Yüz modeli ve takip |
| `hands/tracker.py` | `Frame` | 21 nokta, sağ/sol | El modeli |
| `hands/gestures.py` | el noktaları, zaman | kararlı jest ve olaylar | Histerezis, bekleme, soğuma, sıfırlama |
| `skin/analyzer.py` | tam kare, yüz sonucu | kalite raporu, göstergeler | Tek kare analizi |
| `main.py` | hepsi | ekran | Döngü, modlar, arayüz |

**Tasarım kararları:**

- **Tek kamera akışı ve ortak kare:** Kare bir kez okunur, bir kez küçültülür ve bir kez RGB'ye
  çevrilir; etkin modüller aynı `Frame` nesnesini kullanır.
- **Görüntü boyutu:** Kamera 1280×720 istenir; modellere 640 piksel genişlik verilir; cilt analizi tam
  çözünürlüklü kareden yapılır.
- **Modeller bir kez yüklenir:** Program başında oluşturulur, döngü içinde yeniden oluşturulmaz.
- **Analiz sıklığı:** Yüz ve el her karede, yalnızca etkin modda çalışır; cilt düşük sıklıkta çalışır.
- **Kameranın bırakılması:** `with` yapısı ve `finally` bloğu, hata olsa bile kamerayı ve modelleri kapatır.
- **Yüz veya el yoksa:** Durum satırında açık bir mesaj gösterilir; el kaybolunca etkileşim durumu sıfırlanır.
- **Model dosyası eksikse:** `ModelMissingError` yalnızca ilgili modülü kapatır ve çözüm komutunu yazar;
  diğer modüller çalışmaya devam eder. Segmentasyon modeli yoksa cilt modülü temel yöntemle devam eder.
- **Eşikler tek yerde:** `src/config.py` her eşiğin kaynağını [Belge], [Kaynak] veya [Deney] olarak belirtir.
- **Bağımlılıkların ayrılması:** Çekirdek bağımlılıklar yalnızca dört pakettir. Test aracı
  `requirements-dev.txt` içindedir. Ağır bir derin öğrenme kütüphanesi (PyTorch) çekirdeğe eklenmemiştir;
  böylece ilk kamera dersi büyük bir indirmeye bağlı kalmaz.

**Web sunumu ile ilişki:** Eğitimde görüntü işleme OpenCV ve Python ile öğretilir. Sınıfta kullanılan
web sunumundaki yüz ve el gösterimleri MediaPipe'ın tarayıcı sürümüyle (`@mediapipe/tasks-vision`)
tarayıcıda çalışır; sunum Python kodunu çalıştırmaz ve kamera verisini hiçbir sunucuya göndermez.
Sunum aynı modül adlarını (camera, face, hands, skin), aynı bölge noktalarını ve aynı eşikleri kullanır.

# K. Deneyler ve değerlendirme

## Görev bazlı başarı ölçütleri

| Görev | Ölçüt | Bu çalışmadaki doğrulama |
|---|---|---|
| Kamera açılıyor | `check_setup.py --kamera` 30/30 kare okur | Doğrulama raporuna bakınız |
| Yüz noktaları izleniyor | 478 nokta, yüz kaybında mesaj | Örnek görüntü ve videoyla doğrulandı |
| Pinch bir kez tetikliyor | Bir hareket = bir `pinch_basladi` | Gürültülü sentetik veriyle test edildi |
| El kaybolunca sıfırlama | Tek `el_kayboldu`, pinch bırakılır | Test edildi |
| Düşük kalitede sonuç yok | Bulanık, karanlık, aşırı parlak, döndürülmüş, iki yüz | Örnek görüntü varyantlarıyla doğrulandı |
| Kapanışta kamera bırakılır | `with` dışında `is_open == False`, hata durumunda da | Dosya kaynağıyla test edildi |

## Test senaryoları

| Senaryo | Gözlenecek | Beklenen davranış |
|---|---|---|
| Aydınlık ve loş ortam | Kalite listesi, EAR, jest kararlılığı | Loşta cilt sonucu üretilmez; takip sürer ama titreme artabilir |
| Farklı kamera uzaklıkları (40, 60, 90 cm) | Oranlar, pinch oranı | Oranlar yaklaşık sabit; uzakta "kameraya yaklaşın" |
| Başın dönmesi | Poz açıları, şekil eğilimi | 15° üstünde etiket yerine bekleme mesajı |
| Gözlük, sakal, kısmi örtülme | Bölge kapsaması, doku | Kapsama düşerse sonuç üretilmez; sakal dokuyu yükseltir |
| Sağ ve sol el | Etiket | Deneyle doğrulanır, gerekirse `HANDEDNESS_SWAP` |
| Hızlı hareket | Ham ve yumuşatılmış iz, netlik | Yumuşatılmış iz gecikir; bulanık karede cilt sonucu yok |
| Farklı cilt tonları | Pozlama ve kapsama sonuçları | Uygun ışıkta bütün katılımcılar için analiz üretilmeli; reddedilme oranı tonlara göre not edilir |
| Kamera başka uygulamada açık | Başlangıç mesajı | "Kamera açılamadı" ve olası nedenler |

## Performans

Hedef performans: birleşik uygulamada kamera hızında (genellikle 30 FPS) akıcı görüntü; cilt analizinin
bir saniyenin altında tamamlanması. **Ölçülen performans** yalnızca bu makinede ve yalnızca işlem
süresi için geçerlidir (`scripts/benchmark.py`, 1280×720 kaynak, 640 piksel işleme genişliği, yüz ve el
modülleri etkin, kamera ve ekran gecikmesi dahil değil):

| Donanım ve sürüm | Yüz modeli | El modeli | Yüz + el toplam | Cilt analizi (tek kare) |
|---|---|---|---|---|
| Apple M4, macOS 27, MediaPipe 1.1.1, OpenCV 4.14 | 5,9 ms | 5,4 ms | 11,6 ms | 37 ms (ortanca) |
| Aynı makine, MediaPipe 0.10.21, OpenCV 4.11 (Intel Mac yapılandırması) | 10,7 ms | 17,6 ms | 28,5 ms | 204 ms (ortanca) |

Intel Mac yapılandırması bu çalışmada bir Intel Mac üzerinde değil, aynı paketlerin Apple Silicon
üzerinde çalışan sürümüyle ölçülmüştür. Eğitim sırasında aynı betik her katılımcının bilgisayarında
çalıştırılarak tabloya donanım, çözünürlük ve etkin modül bilgisiyle yeni satırlar eklenecektir.

**Gizlilik ve katılım:** Uygulama görüntüleri varsayılan olarak kaydetmez (`--snapshot` yalnızca açıkça
verildiğinde son ekranı kaydeder) ve hiçbir görüntüyü harici sunucuya göndermez. Kamera kullanmak
istemeyen katılımcılar `--source video.mp4` veya `--source foto.jpg` ile kendi dosyalarını kullanabilir
ya da web sunumundaki "Örnek gösterim" modunu izleyebilir.

# L. Sık karşılaşılan sorunlar

| Belirti | Olası neden | Çözüm |
|---|---|---|
| `AttributeError: module 'mediapipe' has no attribute 'solutions'` | Eski bir örnek kopyalandı | Tasks API kullanılır (`mp.tasks.vision`); projedeki örneklere bakılır |
| `No matching distribution found for mediapipe` | Intel Mac veya desteklenmeyen Python | Intel Mac: `requirements-intel-mac.txt`; Python 3.12 kullanılır |
| `cv2` içe aktarılırken garip hatalar | `opencv-python` ve `opencv-contrib-python` birlikte kurulu | `pip uninstall opencv-python opencv-python-headless`, ardından `pip install -r requirements.txt` |
| "Kamera açılamadı" | Kamera başka uygulamada, izin yok, yanlış numara | Uygulamalar kapatılır, izin verilir, `--source 1` denenir |
| macOS'ta siyah görüntü | 0 numara başka bir kamera (ör. iPhone Süreklilik Kamerası) veya mercek kapalı | Varsayılan `--source auto` görüntü veren kamerayı seçer; elle `--source 1` |
| macOS'ta kamera açılmıyor | Programı başlatan uygulamaya kamera izni verilmemiş | Sistem Ayarları > Gizlilik ve Güvenlik > Kamera; uygulama yeniden başlatılır |
| `CERTIFICATE_VERIFY_FAILED` | python.org macOS kurulumunda sertifika eksik | Sanal ortam içinde çalıştırılır (certifi kullanılır) veya "Install Certificates.command" çalıştırılır |
| `Model dosyası bulunamadı` | Modeller indirilmedi | `python scripts/download_models.py` |
| `Input timestamp must be monotonically increasing` | VIDEO modunda zaman damgası tekrarlandı | `FramePreparer` ve `FrameClock` kullanılır |
| Türkçe harfler "?" görünüyor | `cv2.putText` kullanıldı | `common.draw.put_text` kullanılır |
| Ten rengi mavimsi | BGR kare RGB beklenen yere verildi | `cv2.cvtColor(..., cv2.COLOR_BGR2RGB)` |
| FPS çok düşük | Büyük işleme karesi, gereksiz modüller açık | `PROCESS_WIDTH` 480'e düşürülür, yalnızca gerekli mod açılır |
| Sağ ve sol el ters | Aynalama ve etiket anlamı | `config.HANDEDNESS_SWAP = True` |
| Cilt analizi hep "Uygun görüntü bekleniyor" | Işık, poz veya mesafe | Kalite listesindeki kırmızı satırın önerisi uygulanır |
| PowerShell'de etkinleştirme engelleniyor | Betik çalıştırma ilkesi | cmd kullanılır veya yalnızca o pencere için `-Scope Process` |

# M. Proje geliştirme fikirleri

- Göz kırpmayla uygulama içinde "tıklama" ve yanlış tetiklemeyi ölçen küçük bir kullanılabilirlik deneyi.
- El ile çizilen şekli (daire, kare) kontur özellikleriyle tanıyan kural tabanlı bir sınıflandırıcı.
- Sabit bir renk kartı ve aynı lamba ile standart çekim düzeneği kurup kızarıklık göstergesinin
  günler arası tekrarlanabilirliğini ölçmek.
- One Euro filtresinin parametrelerini ham ve yumuşatılmış iz üzerinde gecikme ve titreme ölçerek ayarlamak.
- Jest kararlılığı için bekleme ve soğuma sürelerini farklı katılımcılarla deneyip sonuçları tabloya dökmek.
- Tarayıcı sürümüyle Python sürümünün aynı videoda verdiği noktaları karşılaştırmak.
- Lisansı uygun, açık bir veri kümesiyle küçük bir sınıflandırıcı eğitip kural tabanlı göstergelerle
  karşılaştırmak (ayrı bir ileri proje olarak).

# N. Kaynakça ve lisans notları

## Kaynaklar (erişim: 19.10.2026)

- Bradski, G. (2000). The OpenCV Library. *Dr. Dobb's Journal*. Kod: <https://github.com/opencv/opencv>
- Lugaresi, C. vd. (2019). MediaPipe: A Framework for Building Perception Pipelines. arXiv:1906.08172.
  Kod: <https://github.com/google-ai-edge/mediapipe>
- MediaPipe Face Landmarker: <https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker>
- MediaPipe Hand Landmarker: <https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker>
- MediaPipe Image Segmenter: <https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter>;
  Selfie Multiclass model kartı: <https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Multiclass%20Segmentation.pdf>
- MediaPipe örnekleri: <https://github.com/google-ai-edge/mediapipe-samples>
- Bazarevsky, V. vd. (2019). BlazeFace: Sub-millisecond Neural Face Detection on Mobile GPUs. arXiv:1907.05047.
- Kartynnik, Y. vd. (2019). Real-time Facial Surface Geometry from Monocular Video on Mobile GPUs. arXiv:1907.06724.
- Zhang, F. vd. (2020). MediaPipe Hands: On-device Real-time Hand Tracking. arXiv:2006.10214.
- Viola, P. ve Jones, M. (2001). Rapid Object Detection using a Boosted Cascade of Simple Features. *CVPR*.
- Otsu, N. (1979). A Threshold Selection Method from Gray-Level Histograms. *IEEE Trans. SMC*, 9(1).
- Soukupová, T. ve Čech, J. (2016). Real-Time Eye Blink Detection using Facial Landmarks. *CVWW*.
- Casiez, G., Roussel, N. ve Vogel, D. (2012). 1€ Filter: A Simple Speed-based Low-pass Filter for Noisy
  Input in Interactive Systems. *CHI*.
- Pech-Pacheco, J. L. vd. (2000). Diatom Autofocusing in Brightfield Microscopy: A Comparative Study. *ICPR*.
- Selvaraju, R. R. vd. (2017). Grad-CAM: Visual Explanations from Deep Networks via Gradient-based
  Localization. *ICCV*.
- Barrett, L. F. vd. (2019). Emotional Expressions Reconsidered: Challenges to Inferring Emotion From Human
  Facial Movements. *Psychological Science in the Public Interest*, 20(1).
- Buolamwini, J. ve Gebru, T. (2018). Gender Shades: Intersectional Accuracy Disparities in Commercial
  Gender Classification. *FAT\**.
- Mitchell, M. vd. (2019). Model Cards for Model Reporting. *FAT\**.
- Prokhorov, K. ve Kalinin, A. A. (2024). Improving Acne Image Grading with Label Distribution Smoothing.
  *ISBI*. arXiv:2403.00268. Kod: <https://github.com/openface-io/acne-lds>
- Wu, X. vd. (2019). Joint Acne Image Grading and Counting via Label Distribution Learning. *ICCV*.
  Veri: <https://github.com/xpwu95/LDL>
- İncelenen diğer depolar: <https://github.com/DurtyDhiana/skin-scan>, <https://github.com/Corerishi/VitalGaze>,
  <https://github.com/cvzone/cvzone>, <https://github.com/opencv/opencv_zoo>

## Lisans notları

| Bileşen | Kod lisansı | Model / veri lisansı | Not |
|---|---|---|---|
| Bu proje (VISION LAB) | Topluluk tarafından seçilecektir; bağımlılıklarla uyumlu seçenekler MIT veya Apache-2.0'dır | — | Depoda henüz `LICENSE` dosyası yoktur |
| OpenCV | Apache-2.0 | Haar XML: Intel License (BSD benzeri) | |
| MediaPipe | Apache-2.0 | Model kartları: Apache-2.0 | Eğitim verisi yayımlanmamış |
| `@mediapipe/tasks-vision` (sunum) | Apache-2.0 | Aynı modeller | Tarayıcıda yerel çalışır |
| NumPy | BSD-3-Clause (ve alt bileşenler) | — | |
| Pillow | MIT-CMU (HPND) | — | |
| React, Vite | MIT | — | Sunum |
| Standart yüz modeli (`shared/canonical_face_478.json`) | Apache-2.0 | — | MediaPipe deposundan |
| acne-lds | MIT | Ağırlık: belirtilmemiş; ACNE04: yalnızca akademik | Entegre edilmedi |
| skin-scan | MIT | Ağırlık yok | Yalnızca yöntem fikri |
| VitalGaze | Lisans yok | Belirsiz | Kullanılmadı |

Ayrıntılı üçüncü taraf bildirimleri `docs/KAYNAKCA_VE_LISANSLAR.md` dosyasındadır. Bu rapordaki
şekiller gerçek kişi görüntüsü içermez; yüz şekilleri MediaPipe'ın standart yüz modelinden, grafikler
sentetik sinyallerden ve proje kodunun kendisinden üretilmiştir.

::: {.landscape}
# Ek: Aday projelerin karşılaştırma tablosu

**Tablo C1.** Aday projelerin karşılaştırılması (kontrol tarihi: 19.10.2026)

| Proje | Bağlantı | Kullanım amacı | Kod lisansı | Model/veri lisansı | Yerel çalışma | CPU uygunluğu | Kurulum zorluğu | Doğrulanmış özellikler | Sınırlamalar | Eğitimdeki rolü |
|---|---|---|---|---|---|---|---|---|---|---|
| OpenCV **[Ç]** | <https://github.com/opencv/opencv> | Kamera, renk, filtre, eşik, morfoloji, kontur, çizim | Apache-2.0 | Yerleşik Haar dosyaları: Intel License (BSD benzeri, dosya başlığında) | Evet | Evet | Kolay | Proje testleri 4.14.0.94, 4.11.0.86 ve 5.0.0.93 ile geçti; Haar yüz tespiti çalıştı | `opencv-python` ile `opencv-contrib-python` aynı ortamda çakışır; `putText` Türkçe karakter çizemez; 4.14 macOS paketi macOS 13+ ister | Temel görüntü işleme katmanı |
| MediaPipe Tasks **[Ç]** | <https://github.com/google-ai-edge/mediapipe> | Yüz (478 nokta) ve el (21 nokta) modelleri | Apache-2.0 | Face Mesh V2, BlazeFace, Hand, Blendshape model kartları: Apache-2.0; eğitim verisi yayımlanmamış | Evet (model indirildikten sonra çevrimdışı) | Evet: yüz 5,9 ms, el 5,4 ms (M4, 640 px) | Kolay; Intel Mac için ayrı sürüm | Aynı kod 1.1.1 ve 0.10.21 ile çalıştı; `mp.solutions` 1.1.1'de yok | 0.10.21'den sonra Intel Mac paketi yok; model kartları gözetim ve kimlik tanımayı kapsam dışı sayar | Öğrenilmiş yüz ve el modelleri |
| Selfie Multiclass Segmenter **[Ç]** | <https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter> | Saç, yüz cildi ve aksesuar piksellerini ayırma | Apache-2.0 (MediaPipe) | Model kartı: Apache-2.0; eğitim verisi yayımlanmamış | Evet | Evet: cilt analizinin tamamı 37 ms | Kolay (16,4 MB) | Örnek portrelerde saç ve yüz cildi ayrıldı | Piksel düzeyinde kusursuz değil; arka ışıkta bozulur; cilt durumu hakkında bilgi vermez | Seviye 2: entegre edilen öğrenilmiş model |
| mediapipe-samples **[K]** | <https://github.com/google-ai-edge/mediapipe-samples> | Resmî örnek uygulamalar | Apache-2.0 | Örnek görseller için ayrı lisans belirtilmemiş | Evet | Evet | Orta | Python not defterleri Tasks API kullanıyor | `raspberry_pi/hand_landmarker/detect.py` `mp.solutions` ve `landmark_pb2` kullanıyor; 1.1.1'de bu içe aktarmalar başarısız | API başvurusu; kod kopyalanmadı |
| OpenCV Zoo YuNet **[B]** | <https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet> | Alternatif yüz dedektörü (`cv2.FaceDetectorYN`) | Apache-2.0 | Model: MIT; eğitim verisi WIDER Face | Evet | Evet | Orta (ONNX ayrıca indirilir) | README: WIDER Face AP 0,88 / 0,87 / 0,75 | Kutu ve 5 nokta verir, 478 nokta yok; OpenCV 5 için dinamik girişli dosya gerekir | Alternatif ve ileri okuma |
| cvzone **[K]** | <https://github.com/cvzone/cvzone> | Yeni başlayanlar için el ve yüz sarmalayıcıları | MIT | MediaPipe modellerine dayanır | Evet | Evet | Kolay | `HandTrackingModule` `mp.solutions.hands` kullanıyor | Son güncelleme 10.05.2024; MediaPipe 0.10.30 ve sonrası ile uyumsuz | Kullanılmadı; eski API örneği |
| skin-scan **[K]** | <https://github.com/DurtyDhiana/skin-scan> | Kural tabanlı cilt haritaları sunan FastAPI servisi | MIT | Model ağırlığı yok | Evet | Evet | Orta (`numpy<2`, `opencv-python-headless==4.8.1.78` sabit) | LAB a*, HSV parlama ve Laplace tabanlı haritalar kodda var | `mp.solutions` kullanıyor; "hydration", "pores", "pigment" adları biyolojik ölçüm çağrıştırıyor; yanak maskesi göz ve ağzı içeriyor; haritalar her görüntüde ayrı ölçekleniyor | Yöntem fikri kaynağı; kod ve adlar alınmadı |
| VitalGaze **[K]** | <https://github.com/Corerishi/VitalGaze> | Web kamerasıyla "sağlık" ve alkol belirtisi analizi | Lisans dosyası yok | Kaynağı belirsiz `alcohol_detection_model.pkl` | Evet | Evet | Zor (çakışan OpenCV paketleri, `mediapipe==0.10.9`) | "Kızarıklık" HSV doygunluk ortalaması olarak hesaplanıyor; sarhoşluk kararı iki eşikten | Bilimsel ve etik açıdan uygun değil; pickle dosyası güvenlik riski | Kullanılmadı; eleştirel değerlendirme örneği |
| acne-lds **[K] [D]** | <https://github.com/openface-io/acne-lds> | Akne şiddeti derecelendirme (ISBI 2024) | MIT | Ağırlıklar Google Drive'da, lisans belirtilmemiş; veri ACNE04 "yalnızca akademik kullanım" | Ağırlık indirilirse | Kısmen: ResNet-50, 224 px'te yaklaşık 4,1 GFLOP | Zor (`torch==1.10.1` sabit, Python 3.9 ve altı) | Çıktı: 4 dereceli sınıf ve 65 kutulu lezyon sayısı dağılımı; kutu veya maske yok | Klinik fotoğraflarla eğitilmiş; web kamerasıyla alan farkı; ağırlıklar bu çalışmada indirilmedi | İleri aşama tartışma örneği; entegre edilmedi |
| HF cilt modelleri **[B]** | <https://huggingface.co/charuka0/acne-multilabel-classifier>, <https://huggingface.co/mufasabrownie/glowlytics-skin-models> | Akne türü; "nem, esneklik" tahmini | Model kartında MIT | Kaggle verisi; UTKFace ve FFHQ (ticari olmayan kullanım koşulları), dil modeli etiketleri | Evet | Evet | Orta | Yalnızca model kartları okundu | Klinik doğrulama yok; kusursuza yakın test sonuçları veri sızıntısı şüphesi doğurur; web kamerasıyla doğrulanamayan çıktılar | Kullanılmadı |
:::
