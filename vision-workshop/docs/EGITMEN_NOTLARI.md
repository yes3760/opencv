# VISION LAB — Eğitmen notları ve oturum akışı

Bu belge `presentation/src/scenes/meta.js` dosyasından `npm run notes` komutuyla üretilir;
sunumdaki "Notlar" paneli ve sunucu penceresi aynı metinleri gösterir.

## Sunumun kullanımı

| İşlem | Kısayol veya yol |
|---|---|
| Sonraki / önceki sahne | Sağ ve sol ok, alttaki ← → düğmeleri, dokunmatik ekranda yatay kaydırma |
| İlk sahne | Home |
| Uygulama içi tam ekran | F (Esc ile çıkılır) |
| Açık katmanları kapatma | Esc (bölüm menüsü, notlar, kod) |
| Notlar paneli | N veya üstteki "Notlar" |
| Bölüm menüsü | M veya üstteki "Bölümler" |
| Sunucu penceresi | Üstteki "Sunucu penceresi": notlar, sıradaki sahne ve geçen süre ayrı pencerede; ana sunumu izler |
| Kodu göster | Alttaki "Kodu göster": Python dosyası, çalıştırma komutu ve kod parçası |

Kısayollar metin alanlarında ve sürgülerde devre dışıdır. Adres çubuğundaki `#/9` gibi sahne
numarası doğrudan o sahneyi açar.

## Oturum öncesi hazırlık (eğitmen)

1. Proje kökünde `python scripts/download_models.py` ve `python scripts/check_setup.py --kamera` çalıştırılır.
2. `presentation` klasöründe `npm install` (bir kez) ve `npm run dev`; sunum `http://localhost:5173` adresinde açılır.
   Kamera yalnızca `localhost` veya HTTPS adresinde açılır; ağ üzerinden IP adresiyle açılan sunumda kamera çalışmaz.
3. Canlı demo sahnelerinden biri (09) açılıp "Kamerayı başlat" ile kamera izni önceden verilir.
4. Projeksiyon bağlıysa "Sunucu penceresi" dizüstü ekranına, sunum projeksiyona alınır ve F ile tam ekran yapılır.
5. Yedek plan: kamera veya model sorununda her canlı demoda "Örnek gösterim" ve "Video dosyası seç" seçenekleri vardır.
6. Mac'te birden fazla kamera varsa (ör. iPhone Süreklilik Kamerası) Python uygulaması `--source auto` ile görüntü veren kamerayı seçer.

## Gizlilik ve katılım

- Kamera kullanımı gönüllüdür; kamerasız katılım için video/fotoğraf dosyası veya örnek gösterim kullanılır.
- Python uygulaması ve sunum görüntü kaydetmez ve hiçbir sunucuya göndermez. `--snapshot` yalnızca açıkça verildiğinde son ekranı kaydeder.
- Cilt bölümünde uyarı metni her zaman görünür: "Eğitim amaçlı görüntü analizi; tıbbi tanı değildir."
- Katılımcıların yüzleri üzerinden kişilik, duygu veya sağlık yorumu yapılmaz; ekranda gösterilen değerler görünüm ölçümüdür.

## Oturum akışı

Her oturum 75 dk eğitim ve uygulama + 15 dk ara + 90 dk eğitim ve uygulama = 180 dk. Toplam 12 saat; 11 saati eğitim ve uygulama.

### Oturum 1: Temeller (180 dk)

Öğrenme çıktısı: Görüntüyü dizi olarak okuyup kural tabanlı bir işleme hattı kurmak

| Başlangıç | Konu | Süre | Sahne | Python dosyası |
|---|---|---|---|---|
| 0:00 | Tanışma, gizlilik ve gönüllülük | 10 dk | 01, 02 | — |
| 0:10 | Kurulum kontrolü | 20 dk | — | `scripts/check_setup.py --kamera` |
| 0:30 | Kamera döngüsü ve FPS | 20 dk | 03 | `examples/01_kamera.py` |
| 0:50 | NumPy dizisi, BGR/RGB, gri, HSV, LAB | 25 dk | 04 | `examples/02_piksel_renk.py` |
| 1:15 | Ara | 15 dk | — | — |
| 1:30 | ROI ve yeniden boyutlandırma | 20 dk | 05 | `examples/03_filtre_esik.py` |
| 1:50 | Gaussian bulanıklık, eşik, Otsu | 25 dk | 05, 06 | `examples/03_filtre_esik.py` |
| 2:15 | Morfoloji ve kontur | 20 dk | 06 | `examples/03_filtre_esik.py` |
| 2:35 | FPS, gecikme; kural tabanlı ve öğrenilmiş yöntem | 15 dk | 03 | — |
| 2:50 | Öğrenci deneyi ve kapanış | 10 dk | 22 | — |

### Oturum 2: Yüz (180 dk)

Öğrenme çıktısı: Noktalardan mesafeden bağımsız ölçüm üretmek ve ölçümün sınırını tanımak

| Başlangıç | Konu | Süre | Sahne | Python dosyası |
|---|---|---|---|---|
| 0:00 | Tekrar | 10 dk | — | — |
| 0:10 | OpenCV ve MediaPipe'ın rolleri, Tasks API | 15 dk | 07 | — |
| 0:25 | Yüz tespiti, kutu, noktalar, Haar karşılaştırması | 25 dk | 08, 09 | `examples/04_yuz_tespiti.py` |
| 0:50 | Takip ve tanıma farkı, hareket izi, EMA | 25 dk | 08, 11 | `examples/05_yuz_takip.py` |
| 1:15 | Ara | 15 dk | — | — |
| 1:30 | Aynalama, koordinatlar, normalize ölçüm | 20 dk | 10 | — |
| 1:50 | EAR, ağız açıklığı, baş yönelimi, blendshape | 30 dk | 09 | `examples/06_yuz_geometrisi.py` |
| 2:20 | Yüz oranları, sınırları, "Bir kamera neyi ölçebilir?" | 20 dk | 12 | `examples/06_yuz_geometrisi.py` |
| 2:40 | Mesafe ve poz deneyi | 20 dk | 12, 22 | `examples/06_yuz_geometrisi.py` |

### Oturum 3: El (180 dk)

Öğrenme çıktısı: Gürültülü model çıktısından güvenilir komut üretmek

| Başlangıç | Konu | Süre | Sahne | Python dosyası |
|---|---|---|---|---|
| 0:00 | Tekrar | 10 dk | — | — |
| 0:10 | 21 el noktası, eklem açıları, parmak durumları | 25 dk | 13 | `examples/07_el_noktalari.py` |
| 0:35 | Sağ/sol etiketi ve aynalama deneyi | 15 dk | 13 | `examples/07_el_noktalari.py` |
| 0:50 | Pinch ve normalize mesafe | 25 dk | 14 | `examples/08_el_jestleri.py` |
| 1:15 | Ara | 15 dk | — | — |
| 1:30 | Histerezis, bekleme ve soğuma süresi, el kaybında sıfırlama | 30 dk | 14 | `src/hands/gestures.py` |
| 2:00 | Sürgü, sürükleme ve çizim | 35 dk | 15 | `examples/08_el_jestleri.py` |
| 2:35 | Tek komut testi ve eşik ayarı | 25 dk | 22 | `src/config.py` |

### Oturum 4: Cilt ve birleşik uygulama (180 dk)

Öğrenme çıktısı: Kaliteye bağlı, açıklanabilir ve sınırları belirtilmiş analiz yapmak

| Başlangıç | Konu | Süre | Sahne | Python dosyası |
|---|---|---|---|---|
| 0:00 | Tekrar | 10 dk | — | — |
| 0:10 | Cilt bölgeleri, dışarıda bırakma, segmentasyon modeli | 25 dk | 16 | `examples/09_cilt_bolgeleri.py` |
| 0:35 | Görüntü kalite kontrolü | 20 dk | 18 | `examples/10_cilt_analizi.py` |
| 0:55 | Görünüm göstergeleri ve ısı haritaları | 20 dk | 18 | `examples/10_cilt_analizi.py` |
| 1:15 | Ara | 15 dk | — | — |
| 1:30 | Işığın etkisi deneyi | 20 dk | 17 | `examples/10_cilt_analizi.py` |
| 1:50 | Kural tabanlı analiz ve öğrenilmiş model; açık kaynak model değerlendirmesi | 20 dk | 19, 20 | — |
| 2:10 | Birleşik uygulama ve mimari | 30 dk | 21, 23 | `src/main.py` |
| 2:40 | Final demo ve sonraki adımlar | 20 dk | 23, 24 | `src/main.py` |

## Tek günlük 6 saatlik kısa sürüm

Toplam 360 dk: 300 dk eğitim ve uygulama, 60 dk ara (15 + 30 + 15). Kurulum önceden tamamlanmış olmalıdır.

| Blok | Süre | Sahneler | Uygulamalı | Yalnızca gösterim |
|---|---|---|---|---|
| 1 | 75 dk | 01, 02, 03, 04, 05, 06 | 01, 02 | 03 (filtre, eşik, morfoloji, kontur) |
| Ara | 15 dk | | | |
| 2 | 80 dk | 07, 08, 09, 10, 12 | 04, 05, 06 (EAR ve poz) | Haar karşılaştırması, One Euro, yüz şekli eğilimi (11) |
| Öğle arası | 30 dk | | | |
| 3 | 75 dk | 13, 14, 15 | 07, 08 (sürgü) | Çizim ve sürükleme, soğuma süresi ayarı |
| Ara | 15 dk | | | |
| 4 | 70 dk | 16, 17, 18, 19, 23, 24 | 09, 10 | Segmentasyon modeli, ısı haritası yorumu, açık kaynak model tartışması (20) |

Kısa sürümde hiçbir cilt modeli eğitilmez; Seviye 2 yalnızca hazır segmentasyon modelinin gösterimi ve akne derecelendirme modelinin neden entegre edilmediğinin tartışmasıdır.

## Sahne notları

### Giriş

#### 01 · VISION LAB — Kameradan Etkileşime

Oturum 1 · yaklaşık 3 dk

- Eğitimin amacı tek cümleyle verilir: kamera görüntüsünün nasıl veriye, ölçüme ve etkileşime dönüştüğünü adım adım görmek.
- Sağdaki yüz, gerçek bir kişinin fotoğrafı değil, MediaPipe'ın standart yüz modelinin döndürülmüş izdüşümüdür; bu nedenle 'Örnek gösterim' etiketi taşır.
- Gizlilik ilkeleri baştan söylenir: kamera gönüllüdür, görüntüler kaydedilmez, hiçbir sunucuya gönderilmez. Kamerasız katılım için video dosyası veya örnek gösterim kullanılabilir.
- Topluluk, üniversite, eğitmen ve tarih bilgileri workshop.config.json dosyasından gelir; boşsa köşeli parantezli yer tutucu görünür.

#### 02 · Öğrenme rotası: tek proje, yedi aşama

Oturum 1 · yaklaşık 4 dk

- Yedi aşama tek bir projeyi büyütür; her aşamanın examples/ klasöründe tek başına çalışan bir dosyası vardır.
- Aşamalara tıklandığında ilgili dosya ve öğrenme çıktısı görünür. Dört oturumun hangi aşamaları kapsadığı alttaki çubukta gösterilir.
- Her oturum 75 + 15 (ara) + 90 dakikadır; toplam 12 saatin 11 saati eğitim ve uygulamadır.

### Temeller

#### 03 · Kameranın gördüğü veri: sayılardan oluşan bir dizi

Oturum 1 · yaklaşık 8 dk

- Yakınlaştırma sürgüsü sağa çekildikçe görüntü piksel hücrelerine ayrılır; yeterince yakında her hücrenin B, G, R değerleri görünür.
- Fare bir hücrenin üzerine getirildiğinde (x, y) konumu ve frame[y, x] değeri okunur. Önce satır (y), sonra sütun (x) yazıldığı vurgulanır.
- Alttaki şerit, kameranın bir 'diziler akışı' olduğunu gösterir: 30 FPS'te kare başına yaklaşık 33 ms bütçe vardır. Şeritteki FPS değeri tarayıcının çizim hızıdır, kamera ölçümü değildir.
- Python karşılığı: examples/01_kamera.py; frame.shape ve frame.dtype ekrana yazdırılır.

Kod: `examples/01_kamera.py` · Çalıştırma: `python examples/01_kamera.py`

#### 04 · Renk kanalları ve renk uzayları

Oturum 1 · yaklaşık 10 dk

- 'Kanalları ayır' düğmesi üç kanalı ayrı katmanlar olarak kaydırır, tekrar basınca birleştirir.
- 'BGR'yi RGB sanmak' anahtarı, dönüşüm yapılmadan modele verilen bir karede ten renklerinin neden mavimsi göründüğünü gösterir.
- Renk seçicide aynı rengin RGB, HSV (OpenCV ölçeği: H 0-179) ve LAB değerleri yan yana okunur. Parlaklık sürgüsüyle RGB'nin üç kanalının birlikte değiştiği, HSV'de ise renk tonunun sabit kaldığı gösterilir.
- LAB'daki a* kanalı cilt bölümünde yeniden kullanılacaktır; burada 'yeşil-kırmızı ekseni' olarak tanıtılır.

Kod: `examples/02_piksel_renk.py` · Çalıştırma: `python examples/02_piksel_renk.py`

#### 05 · ROI, boyut ve bulanıklaştırma

Oturum 1 · yaklaşık 8 dk

- Görüntü üzerinde fareyle sürüklenerek bir ilgi bölgesi (ROI) seçilir; sağdaki kod satırı ve dizi boyutu canlı güncellenir.
- ROI'nin bir kopya değil görünüm olduğu, üzerine çizim yapınca ana karenin de değiştiği söylenir.
- Ölçek sürgüsü küçültmenin ayrıntıyı nasıl kaybettirdiğini, bulanıklık sürgüsü Gaussian çekirdeğinin etkisini gösterir.
- Buradaki işlemler tarayıcıda JavaScript ile benzetilmiştir; eğitimde aynı adımlar OpenCV ile yapılır.

Kod: `examples/03_filtre_esik.py` · Çalıştırma: `python examples/03_filtre_esik.py`

#### 06 · Eşikleme, morfoloji ve kontur

Oturum 1 · yaklaşık 10 dk

- Eşik sürgüsü elle değiştirilir, ardından 'Otsu' düğmesiyle eşiğin histogramdan otomatik seçilmesi gösterilir.
- Açma işleminin küçük lekeleri, kapama işleminin küçük delikleri temizlediği; kontur sayısının buna göre değiştiği izlenir.
- Gürültü sürgüsü artırıldığında sabit kuralın ne kadar çabuk bozulduğu gösterilir; bu, öğrenilmiş modellere geçişin gerekçesidir.

Kod: `examples/03_filtre_esik.py` · Çalıştırma: `python examples/03_filtre_esik.py`

#### 07 · OpenCV ve MediaPipe'ın rolleri

Oturum 2 · yaklaşık 8 dk

- Hat üzerindeki her blok hangi kütüphanenin işi olduğunu renkle gösterir: OpenCV (turkuaz) görüntüyü okur, dönüştürür ve çizer; MediaPipe (mavi) öğrenilmiş modeli çalıştırır.
- 'Kural tabanlı' ve 'Öğrenilmiş' anahtarları, hangi adımın insan yazımı kural, hangisinin eğitilmiş model olduğunu vurgular.
- Sürüm notu: mediapipe 1.1.1'de eski mp.solutions arayüzü yoktur. İnternetteki örneklerin çoğu bu yüzden çalışmaz; projede yalnızca Tasks API kullanılır.
- Intel Mac kullanan öğrenciler için requirements-intel-mac.txt (mediapipe 0.10.21) hatırlatılır.

Kod: `src/common/frame.py` · Çalıştırma: `python examples/04_yuz_tespiti.py`

### Yüz

#### 08 · Tespit, takip ve tanıma aynı şey değildir

Oturum 2 · yaklaşık 8 dk

- Üç panel aynı sentetik hareketi gösterir. Tespit her karede kutu üretir; takip kutulara iz numarası verir; tanıma bu eğitimin parçası değildir.
- Bir nokta kadrajdan çıkıp tekrar girdiğinde yeni iz numarası aldığı gösterilir: iz numarası kişinin kimliği değildir.
- MediaPipe model kartları gözetim ve kimlik tanımayı açıkça kapsam dışı sayar.

Kod: `src/face/tracker.py` · Çalıştırma: `python examples/05_yuz_takip.py --max-faces 2`

#### 09 · Canlı demo A: Yüz noktaları ve hareket izi

Oturum 2 · yaklaşık 12 dk · canlı demo (kamera isteğe bağlı)

- 'Kamerayı başlat' düğmesine basılır; tarayıcı izin ister. Görüntü yalnızca bu bilgisayarda işlenir.
- Kutu, konturlar ve ham (gri) ile yumuşatılmış (turkuaz) iz görünür. Baş yavaşça hareket ettirilerek iki iz karşılaştırılır.
- Yüz kadrajdan çıkınca durum satırında 'Yüz bulunamadı' görünür; iz birkaç kare sonra temizlenir.
- İzin reddedilirse veya kamera başka uygulamadaysa açıklayıcı bir ekran çıkar; 'Örnek gösterim' ile anlatım sürdürülür. Sahneden çıkınca kamera otomatik kapanır.
- Python karşılığı: examples/04_yuz_tespiti.py ve 05_yuz_takip.py.

Kod: `examples/04_yuz_tespiti.py` · Çalıştırma: `python examples/04_yuz_tespiti.py`

#### 10 · Normalize ölçüm ve aynalama

Oturum 2 · yaklaşık 8 dk

- Uzaklık sürgüsü değiştikçe piksel mesafeleri büyüyüp küçülür, oran ise sabit kalır: ölçümler bu yüzden yüz genişliğine bölünür.
- 'Ayna' anahtarı açıldığında ekrandaki görüntü çevrilir ama 'kişinin sol gözü' etiketi kişinin gerçek sol gözünde kalır; projede model aynalanmamış kareyi görür, ayna yalnızca ekrana uygulanır.
- z değeri santimetre değildir: Face Mesh V2 model kartına göre yüzün kütle merkezine göreli ve yüz genişliğiyle ölçeklidir.

Kod: `src/common/app.py` · Çalıştırma: `python examples/06_yuz_geometrisi.py`

#### 11 · Ham ve yumuşatılmış iz

Oturum 2 · yaklaşık 7 dk

- Hedef nokta sabit bir yolda hareket eder; üzerine ölçüm gürültüsü eklenir. Gri çizgi ham ölçümdür, turkuaz çizgi EMA çıktısıdır.
- α küçüldükçe titreme azalır ama gecikme artar; panelde ikisi de sayı olarak okunur. One Euro filtresi hıza göre bu dengeyi kendisi kurar.
- Bu sahnedeki değerler sentetik sinyalden hesaplanır; kamera ölçümü değildir.

Kod: `src/common/smoothing.py` · Çalıştırma: `python examples/05_yuz_takip.py`

#### 12 · Yüz geometrisi: ölçülebilenler ve sınırlar

Oturum 2 · yaklaşık 10 dk

- Dönüş sürgüsü artırıldıkça uzunluk/genişlik oranının yükseldiği görülür; 30 derecede oran yaklaşık yüzde 12 artar. Etiketler bu yüzden yalnızca önden pozda üretilir.
- Şekil eğilimleri standart sınıflar değildir. Yüz ağının üst noktası saç çizgisi değil alnın ortasıdır.
- Sağdaki iki sütun 'Bir kamera neyi ölçebilir?' tartışmasını açar: gözlenebilir hareketler ölçülür; kişilik, zekâ, güvenilirlik veya duygu çıkarımı yapılmaz. Gülümseme sinyali içsel mutluluğun kanıtı değildir.

Kod: `examples/06_yuz_geometrisi.py` · Çalıştırma: `python examples/06_yuz_geometrisi.py`

### El

#### 13 · El işaret noktaları ve parmak durumları

Oturum 3 · yaklaşık 10 dk

- Sentetik elde her parmağın bükülmesi sürgülerle değiştirilir; orta eklem açısı ve 'açık/kapalı/belirsiz' durumu canlı hesaplanır.
- Açı kullanmanın nedeni: 'uç eklemin üstünde mi?' kuralı el döndüğünde bozulur. Eğim sürgüsüyle el döndürülerek açının değişmediği gösterilir.
- Nokta numaraları: 0 bilek, 4 başparmak ucu, 8 işaret ucu. Jest adı parmak durumlarından üretilir.

Kod: `src/hands/gestures.py` · Çalıştırma: `python examples/07_el_noktalari.py`

#### 14 · Jest kararlılığı: bir hareket, bir komut

Oturum 3 · yaklaşık 10 dk

- Üstteki sinyal, parmaklar birbirine yaklaşırken ölçülen gürültülü pinch mesafesidir. İki şerit aynı sinyalden üretilen komutları karşılaştırır.
- Tek eşik, değer eşik çevresinde titredikçe defalarca komut üretir. Histerezis (giriş 0,25, çıkış 0,40) ve 120 ms bekleme süresi tek komut üretir.
- Gürültü ve kararsızlık sürgüleri artırılarak tek eşiğin komut sayısının nasıl patladığı gösterilir.
- El kaybolursa 300 ms sonra durum sıfırlanır; böylece eski bir basılı tutma devam etmez.

Kod: `src/hands/gestures.py` · Çalıştırma: `python examples/08_el_jestleri.py`

#### 15 · Canlı demo B: Pinch ile sürgü ve sürükleme

Oturum 3 · yaklaşık 12 dk · canlı demo (kamera isteğe bağlı)

- Kamera başlatılır; işaret parmağı ucu imleç olur. Sürgünün tutamacı üzerinde pinch yapılıp sürüklenir; kutu da pinch ile taşınır.
- Pinch çubuğundaki giriş ve çıkış çizgileri histerezisi gösterir. Komut sayacı bir hareketin yalnızca bir komut ürettiğini doğrular.
- El kadrajdan çıkınca 'El kayboldu: durum sıfırlandı' görünür ve sürüklenen öğe bırakılır.
- İşletim sisteminin faresi kontrol edilmez; bütün etkileşim uygulamanın içindedir.

Kod: `examples/08_el_jestleri.py` · Çalıştırma: `python examples/08_el_jestleri.py`

### Cilt

#### 16 · Cilt bölgesi çıkarma

Oturum 4 · yaklaşık 8 dk

- Katmanlar sırayla açılır: yüz ağı, alın ve yanak çokgenleri, göz/kaş/dudak dışlaması, kenardan içeri çekme ve saç maskesi.
- Bölge adları kişinin kendi sağına göredir; aynalanmamış görüntüde kişinin sağ yanağı solda görünür.
- Python uygulamasında saç ve aksesuarlar Selfie Multiclass segmentasyon modeliyle ayrılır; model yoksa koyu pikselleri atan renk tutarlılığı yöntemi kullanılır.

Kod: `src/skin/regions.py` · Çalıştırma: `python examples/09_cilt_bolgeleri.py`

#### 17 · Işığın etkisi: cilt aynı, sayı farklı

Oturum 4 · yaklaşık 8 dk

- Sentetik cilt yaması sabittir; yalnızca ışığın rengi, şiddeti ve yönü değiştirilir.
- Sıcak ışıkta mutlak a* değeri belirgin biçimde artar; yan ışıkta iki yarı arasındaki renk farkı (ΔE) büyür. Cilt değişmemiştir.
- Bu yüzden farklı günlerde standart ışık ve kamera ayarları olmadan alınan ölçümler gerçek bir değişim gibi karşılaştırılmaz.
- Python uygulamasında bir fotoğrafın renkleri sıcak ışık yönünde kaydırıldığında alnın a* değeri 15,7'den 24,2'ye çıkmıştır.

Kod: `src/skin/metrics.py` · Çalıştırma: `python examples/10_cilt_analizi.py`

#### 18 · Canlı demo C: Kalite kontrolü ve açıklanabilir harita

Oturum 4 · yaklaşık 12 dk · canlı demo (kamera isteğe bağlı)

- Kamera başlatılır, kişi önden ve iyi ışıkta durur, 'Kare al' düğmesine basılır. Analiz tek kare üzerinde yapılır.
- Kalite listesindeki bir satır kırmızıysa sonuç üretilmez ve neden yazılır: baş döndürülerek veya ortam karartılarak bu davranış gösterilir.
- Isı haritası yalnızca bölge maskesi içinde ve sabit aralıkla (Δa* -10 ile +10) renklendirilir. Uyarı metni her zaman görünür.
- Tarayıcı demosu saç ayrımı için renk tutarlılığı yöntemini kullanır; segmentasyon modeli Python uygulamasındadır. Görüntü kaydedilmez.

Kod: `src/skin/analyzer.py` · Çalıştırma: `python examples/10_cilt_analizi.py`

#### 19 · Kural tabanlı analiz ve öğrenilmiş model

Oturum 4 · yaklaşık 8 dk

- Üç kart aynı sentetik görüntü üzerinde sınıflandırma, tespit ve segmentasyonun farkını gösterir.
- Entegre edilen öğrenilmiş model Selfie Multiclass Segmenter'dır: her piksele sınıf verir, cildin durumu hakkında bir şey söylemez.
- acne-lds değerlendirilmiş ama entegre edilmemiştir: ağırlık lisansı belirsiz, veri akademik kullanımla sınırlı, klinik fotoğraflardan web kamerasına alan farkı var. Bir sınıflandırıcının çıktısına kutu çizmek modelin üretmediği bilgiyi uydurmaktır.
- Grad-CAM benzeri haritalar modelin dikkat ettiği bölgeyi kabaca gösterir; lezyon segmentasyonu değildir.

Kod: `src/skin/segmenter.py` · Çalıştırma: `python examples/09_cilt_bolgeleri.py`

### Proje

#### 20 · GitHub kaynaklarının karşılaştırılması

Oturum 4 · yaklaşık 6 dk

- Satıra tıklandığında doğrulanan özellikler ve sınırlamalar açılır. Filtreler kullanılan, fikir alınan ve kullanılmayan kaynakları ayırır.
- Kod lisansı, model ağırlığı lisansı ve veri lisansı ayrı ayrı değerlendirilmiştir; herkese açık bir depo serbest kullanım izni anlamına gelmez.
- Yıldız sayısı kalite ölçütü değildir; kontrol tarihi 19.10.2026'dır. Ayrıntılı tablo öğrenci raporunun ekindedir.

#### 21 · Birleşik mimari: tek kamera, ortak kare

Oturum 4 · yaklaşık 8 dk

- Mod düğmeleri hangi modüllerin çalıştığını değiştirir; cilt modülünün düşük sıklıkta çalıştığı ayrı renkle gösterilir.
- Bir modüle tıklandığında girdi, çıktı ve sorumluluğu görünür. Modül adları Python projesindeki klasörlerle aynıdır: camera, common, face, hands, skin.
- Eksik model yalnızca kendi modülünü kapatır; kamera her durumda with yapısıyla bırakılır.

Kod: `src/main.py` · Çalıştırma: `python src/main.py`

#### 22 · Öğrenci görevleri ve deneyler

Oturum 1-4 · yaklaşık 5 dk

- Her oturumun görevleri işaretlenebilir; işaretler yalnızca bu tarayıcıda saklanır.
- Deneylerin amacı ölçümün sınırını görmektir: ışık, mesafe, poz ve eşik değişikliklerinin sonuca etkisi not edilir.
- Performans tablosu için scripts/benchmark.py her öğrencinin bilgisayarında çalıştırılabilir.

#### 23 · Final demo: yüz ve el birlikte

Oturum 4 · yaklaşık 10 dk · canlı demo (kamera isteğe bağlı)

- Kamera başlatılır. Yüz konturları ve el imleci aynı anda görünür; üstteki mod düğmeleri işaret parmağıyla üzerine gelinip pinch yapılarak değiştirilir.
- Bu, Python'daki src/main.py uygulamasının tarayıcıdaki sadeleştirilmiş eşidir. Python uygulaması: python src/main.py
- Her iki model aynı karede çalıştığı için panelde yüz ve el model süreleri ayrı ayrı görünür; bunlar tarayıcıda o an ölçülen değerlerdir.

Kod: `src/main.py` · Çalıştırma: `python src/main.py`

#### 24 · Kaynaklar ve sonraki adımlar

Oturum 4 · yaklaşık 4 dk

- Kaynaklar öğrenci raporunun N bölümünde tıklanabilir bağlantılarla yer alır.
- Proje geliştirme fikirleri arasından bir tanesi seçilip küçük bir deney raporu hazırlanabilir.
- İletişim ve depo bağlantısı workshop.config.json dosyasından gelir.
