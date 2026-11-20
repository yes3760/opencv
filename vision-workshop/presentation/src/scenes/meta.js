// Sahne bilgileri: başlık, bölüm, oturum, eğitmen notları ve "Kodu göster" içeriği.
// Bu dosya hem sunumda hem de docs/EGITMEN_NOTLARI.md üretiminde (scripts/export-notes.mjs) kullanılır.
// Kod parçaları Python projesindeki dosyalarla aynıdır (kısaltılmış olabilir).

export const SECTIONS = ["Giriş", "Temeller", "Yüz", "El", "Cilt", "Proje"];

export const SCENES = [
  {
    id: "acilis", section: "Giriş", session: "1", minutes: 3,
    title: "VISION LAB — Kameradan Etkileşime",
    notes: [
      "Eğitimin amacı tek cümleyle verilir: kamera görüntüsünün nasıl veriye, ölçüme ve etkileşime dönüştüğünü adım adım görmek.",
      "Sağdaki yüz, gerçek bir kişinin fotoğrafı değil, MediaPipe'ın standart yüz modelinin döndürülmüş izdüşümüdür; bu nedenle 'Örnek gösterim' etiketi taşır.",
      "Gizlilik ilkeleri baştan söylenir: kamera gönüllüdür, görüntüler kaydedilmez, hiçbir sunucuya gönderilmez. Kamerasız katılım için video dosyası veya örnek gösterim kullanılabilir.",
      "Topluluk, üniversite, eğitmen ve tarih bilgileri workshop.config.json dosyasından gelir; boşsa köşeli parantezli yer tutucu görünür.",
    ],
  },
  {
    id: "rota", section: "Giriş", session: "1", minutes: 4,
    title: "Öğrenme rotası: tek proje, yedi aşama",
    notes: [
      "Yedi aşama tek bir projeyi büyütür; her aşamanın examples/ klasöründe tek başına çalışan bir dosyası vardır.",
      "Aşamalara tıklandığında ilgili dosya ve öğrenme çıktısı görünür. Dört oturumun hangi aşamaları kapsadığı alttaki çubukta gösterilir.",
      "Her oturum 75 + 15 (ara) + 90 dakikadır; toplam 12 saatin 11 saati eğitim ve uygulamadır.",
    ],
  },
  {
    id: "veri", section: "Temeller", session: "1", minutes: 8,
    title: "Kameranın gördüğü veri: sayılardan oluşan bir dizi",
    notes: [
      "Yakınlaştırma sürgüsü sağa çekildikçe görüntü piksel hücrelerine ayrılır; yeterince yakında her hücrenin B, G, R değerleri görünür.",
      "Fare bir hücrenin üzerine getirildiğinde (x, y) konumu ve frame[y, x] değeri okunur. Önce satır (y), sonra sütun (x) yazıldığı vurgulanır.",
      "Alttaki şerit, kameranın bir 'diziler akışı' olduğunu gösterir: 30 FPS'te kare başına yaklaşık 33 ms bütçe vardır. Şeritteki FPS değeri tarayıcının çizim hızıdır, kamera ölçümü değildir.",
      "Python karşılığı: examples/01_kamera.py; frame.shape ve frame.dtype ekrana yazdırılır.",
    ],
    code: {
      file: "examples/01_kamera.py", run: "python examples/01_kamera.py",
      snippet: `cap = cv2.VideoCapture(0)
ok, frame = cap.read()            # frame bir NumPy dizisidir
print(frame.shape, frame.dtype)   # (720, 1280, 3) uint8
b, g, r = frame[100, 200]         # önce satır (y), sonra sütun (x)
cap.release()                     # kamera ışığı sönmeli`,
    },
  },
  {
    id: "renk", section: "Temeller", session: "1", minutes: 10,
    title: "Renk kanalları ve renk uzayları",
    notes: [
      "'Kanalları ayır' düğmesi üç kanalı ayrı katmanlar olarak kaydırır, tekrar basınca birleştirir.",
      "'BGR'yi RGB sanmak' anahtarı, dönüşüm yapılmadan modele verilen bir karede ten renklerinin neden mavimsi göründüğünü gösterir.",
      "Renk seçicide aynı rengin RGB, HSV (OpenCV ölçeği: H 0-179) ve LAB değerleri yan yana okunur. Parlaklık sürgüsüyle RGB'nin üç kanalının birlikte değiştiği, HSV'de ise renk tonunun sabit kaldığı gösterilir.",
      "LAB'daki a* kanalı cilt bölümünde yeniden kullanılacaktır; burada 'yeşil-kırmızı ekseni' olarak tanıtılır.",
    ],
    code: {
      file: "examples/02_piksel_renk.py", run: "python examples/02_piksel_renk.py",
      snippet: `rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)   # MediaPipe RGB bekler
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 0.299 R + 0.587 G + 0.114 B
hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)   # H: 0-179, S ve V: 0-255
lab  = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)   # 8 bit: L*255/100, a+128, b+128`,
    },
  },
  {
    id: "roi", section: "Temeller", session: "1", minutes: 8,
    title: "ROI, boyut ve bulanıklaştırma",
    notes: [
      "Görüntü üzerinde fareyle sürüklenerek bir ilgi bölgesi (ROI) seçilir; sağdaki kod satırı ve dizi boyutu canlı güncellenir.",
      "ROI'nin bir kopya değil görünüm olduğu, üzerine çizim yapınca ana karenin de değiştiği söylenir.",
      "Ölçek sürgüsü küçültmenin ayrıntıyı nasıl kaybettirdiğini, bulanıklık sürgüsü Gaussian çekirdeğinin etkisini gösterir.",
      "Buradaki işlemler tarayıcıda JavaScript ile benzetilmiştir; eğitimde aynı adımlar OpenCV ile yapılır.",
    ],
    code: {
      file: "examples/03_filtre_esik.py", run: "python examples/03_filtre_esik.py",
      snippet: `small = cv2.resize(frame, (400, 225), interpolation=cv2.INTER_AREA)
roi = small[y1:y2, x1:x2]                    # dilim: kopya değil görünüm
gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)  # çekirdek tek sayı olmalı`,
    },
  },
  {
    id: "esik", section: "Temeller", session: "1", minutes: 10,
    title: "Eşikleme, morfoloji ve kontur",
    notes: [
      "Eşik sürgüsü elle değiştirilir, ardından 'Otsu' düğmesiyle eşiğin histogramdan otomatik seçilmesi gösterilir.",
      "Açma işleminin küçük lekeleri, kapama işleminin küçük delikleri temizlediği; kontur sayısının buna göre değiştiği izlenir.",
      "Gürültü sürgüsü artırıldığında sabit kuralın ne kadar çabuk bozulduğu gösterilir; bu, öğrenilmiş modellere geçişin gerekçesidir.",
    ],
    code: {
      file: "examples/03_filtre_esik.py", run: "python examples/03_filtre_esik.py",
      snippet: `t, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)   # lekeleri sil
cleaned = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel) # delikleri kapat
contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)`,
    },
  },
  {
    id: "roller", section: "Temeller", session: "2", minutes: 8,
    title: "OpenCV ve MediaPipe'ın rolleri",
    notes: [
      "Hat üzerindeki her blok hangi kütüphanenin işi olduğunu renkle gösterir: OpenCV (turkuaz) görüntüyü okur, dönüştürür ve çizer; MediaPipe (mavi) öğrenilmiş modeli çalıştırır.",
      "'Kural tabanlı' ve 'Öğrenilmiş' anahtarları, hangi adımın insan yazımı kural, hangisinin eğitilmiş model olduğunu vurgular.",
      "Sürüm notu: mediapipe 1.1.1'de eski mp.solutions arayüzü yoktur. İnternetteki örneklerin çoğu bu yüzden çalışmaz; projede yalnızca Tasks API kullanılır.",
      "Intel Mac kullanan öğrenciler için requirements-intel-mac.txt (mediapipe 0.10.21) hatırlatılır.",
    ],
    code: {
      file: "src/common/frame.py", run: "python examples/04_yuz_tespiti.py",
      snippet: `bgr = resize_to_width(full_bgr, 640)                 # OpenCV
rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)            # OpenCV
mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
result = landmarker.detect_for_video(mp_image, timestamp_ms)   # MediaPipe`,
    },
  },
  {
    id: "takip", section: "Yüz", session: "2", minutes: 8,
    title: "Tespit, takip ve tanıma aynı şey değildir",
    notes: [
      "Üç panel aynı sentetik hareketi gösterir. Tespit her karede kutu üretir; takip kutulara iz numarası verir; tanıma bu eğitimin parçası değildir.",
      "Bir nokta kadrajdan çıkıp tekrar girdiğinde yeni iz numarası aldığı gösterilir: iz numarası kişinin kimliği değildir.",
      "MediaPipe model kartları gözetim ve kimlik tanımayı açıkça kapsam dışı sayar.",
    ],
    code: {
      file: "src/face/tracker.py", run: "python examples/05_yuz_takip.py --max-faces 2",
      snippet: `for track in self._tracks:                 # en yakın merkez eşleştirmesi
    d = distance(center, track.last_center)
    if d < best_dist:
        best, best_dist = track, d
if best is None:                            # eşleşme yoksa yeni iz numarası
    best = _Track(self._next_id, center, ...)
    self._next_id += 1`,
    },
  },
  {
    id: "demo-yuz", section: "Yüz", session: "2", minutes: 12, camera: true,
    title: "Canlı demo A: Yüz noktaları ve hareket izi",
    notes: [
      "'Kamerayı başlat' düğmesine basılır; tarayıcı izin ister. Görüntü yalnızca bu bilgisayarda işlenir.",
      "Kutu, konturlar ve ham (gri) ile yumuşatılmış (turkuaz) iz görünür. Baş yavaşça hareket ettirilerek iki iz karşılaştırılır.",
      "Yüz kadrajdan çıkınca durum satırında 'Yüz bulunamadı' görünür; iz birkaç kare sonra temizlenir.",
      "İzin reddedilirse veya kamera başka uygulamadaysa açıklayıcı bir ekran çıkar; 'Örnek gösterim' ile anlatım sürdürülür. Sahneden çıkınca kamera otomatik kapanır.",
      "Python karşılığı: examples/04_yuz_tespiti.py ve 05_yuz_takip.py.",
    ],
    code: {
      file: "examples/04_yuz_tespiti.py", run: "python examples/04_yuz_tespiti.py",
      snippet: `with Camera(args.source) as cam, FaceTracker() as faces:
    while loop.running:
        frame = prepare(cam.read())          # küçült, RGB, mp.Image
        result = faces.process(frame)        # 478 nokta, kutu, iz
        canvas = Canvas(frame, mirror=True)
        for face in result.faces:            # 1) şekiller
            draw_face(canvas.image, canvas.pts(face.points), canvas.pts(face.box))
        canvas.flip()                        # 2) ayna
        status_line(canvas.image, result.status)   # 3) yazılar`,
    },
  },
  {
    id: "normalize", section: "Yüz", session: "2", minutes: 8,
    title: "Normalize ölçüm ve aynalama",
    notes: [
      "Uzaklık sürgüsü değiştikçe piksel mesafeleri büyüyüp küçülür, oran ise sabit kalır: ölçümler bu yüzden yüz genişliğine bölünür.",
      "'Ayna' anahtarı açıldığında ekrandaki görüntü çevrilir ama 'kişinin sol gözü' etiketi kişinin gerçek sol gözünde kalır; projede model aynalanmamış kareyi görür, ayna yalnızca ekrana uygulanır.",
      "z değeri santimetre değildir: Face Mesh V2 model kartına göre yüzün kütle merkezine göreli ve yüz genişliğiyle ölçeklidir.",
    ],
    code: {
      file: "src/common/app.py", run: "python examples/06_yuz_geometrisi.py",
      snippet: `points = to_pixels(landmarks, width, height)   # normalize -> piksel
ratio = distance(points[10], points[152]) / distance(points[234], points[454])

canvas = Canvas(frame, mirror=True)
draw_face(canvas.image, canvas.pts(points))     # 1) aynalanmamış görüntüye şekil
canvas.flip()                                   # 2) ayna
put_text(canvas.image, "sol göz", canvas.screen(points[263]))  # 3) yazı`,
    },
  },
  {
    id: "iz", section: "Yüz", session: "2", minutes: 7,
    title: "Ham ve yumuşatılmış iz",
    notes: [
      "Hedef nokta sabit bir yolda hareket eder; üzerine ölçüm gürültüsü eklenir. Gri çizgi ham ölçümdür, turkuaz çizgi EMA çıktısıdır.",
      "α küçüldükçe titreme azalır ama gecikme artar; panelde ikisi de sayı olarak okunur. One Euro filtresi hıza göre bu dengeyi kendisi kurar.",
      "Bu sahnedeki değerler sentetik sinyalden hesaplanır; kamera ölçümü değildir.",
    ],
    code: {
      file: "src/common/smoothing.py", run: "python examples/05_yuz_takip.py",
      snippet: `class EMA:
    def update(self, measurement):
        if self.value is None:
            self.value = measurement
        else:   # yeni = alpha * ölçüm + (1 - alpha) * eski
            self.value = self.alpha * measurement + (1 - self.alpha) * self.value
        return self.value`,
    },
  },
  {
    id: "geometri", section: "Yüz", session: "2", minutes: 10,
    title: "Yüz geometrisi: ölçülebilenler ve sınırlar",
    notes: [
      "Dönüş sürgüsü artırıldıkça uzunluk/genişlik oranının yükseldiği görülür; 30 derecede oran yaklaşık yüzde 12 artar. Etiketler bu yüzden yalnızca önden pozda üretilir.",
      "Şekil eğilimleri standart sınıflar değildir. Yüz ağının üst noktası saç çizgisi değil alnın ortasıdır.",
      "Sağdaki iki sütun 'Bir kamera neyi ölçebilir?' tartışmasını açar: gözlenebilir hareketler ölçülür; kişilik, zekâ, güvenilirlik veya duygu çıkarımı yapılmaz. Gülümseme sinyali içsel mutluluğun kanıtı değildir.",
    ],
    code: {
      file: "examples/06_yuz_geometrisi.py", run: "python examples/06_yuz_geometrisi.py",
      snippet: `if not is_frontal(face.pose):
    return "Uygun görüntü bekleniyor: başınızı düz tutup kameraya bakın."
ratios = face_ratios(face.points)
history.append(ratios["uzunluk/genişlik"])
if len(history) < 20 or np.std(history) > 0.02:
    return "Uygun görüntü bekleniyor: birkaç saniye hareketsiz kalın."
return f"Yaklaşık: {approximate_shape_tendency(ratios)}"`,
    },
  },
  {
    id: "el", section: "El", session: "3", minutes: 10,
    title: "El işaret noktaları ve parmak durumları",
    notes: [
      "Sentetik elde her parmağın bükülmesi sürgülerle değiştirilir; orta eklem açısı ve 'açık/kapalı/belirsiz' durumu canlı hesaplanır.",
      "Açı kullanmanın nedeni: 'uç eklemin üstünde mi?' kuralı el döndüğünde bozulur. Eğim sürgüsüyle el döndürülerek açının değişmediği gösterilir.",
      "Nokta numaraları: 0 bilek, 4 başparmak ucu, 8 işaret ucu. Jest adı parmak durumlarından üretilir.",
    ],
    code: {
      file: "src/hands/gestures.py", run: "python examples/07_el_noktalari.py",
      snippet: `a_pip = angle_deg(points[mcp], points[pip], points[dip])
if a_pip >= config.FINGER_EXTENDED_DEG:      # 150 derece
    states[name] = True                       # açık
elif a_pip <= config.FINGER_FOLDED_DEG:      # 120 derece
    states[name] = False                      # kapalı
else:
    states[name] = None                       # belirsiz`,
    },
  },
  {
    id: "kararlilik", section: "El", session: "3", minutes: 10,
    title: "Jest kararlılığı: bir hareket, bir komut",
    notes: [
      "Üstteki sinyal, parmaklar birbirine yaklaşırken ölçülen gürültülü pinch mesafesidir. İki şerit aynı sinyalden üretilen komutları karşılaştırır.",
      "Tek eşik, değer eşik çevresinde titredikçe defalarca komut üretir. Histerezis (giriş 0,25, çıkış 0,40) ve 120 ms bekleme süresi tek komut üretir.",
      "Gürültü ve kararsızlık sürgüleri artırılarak tek eşiğin komut sayısının nasıl patladığı gösterilir.",
      "El kaybolursa 300 ms sonra durum sıfırlanır; böylece eski bir basılı tutma devam etmez.",
    ],
    code: {
      file: "src/hands/gestures.py", run: "python examples/08_el_jestleri.py",
      snippet: `class Hysteresis:
    def update(self, value):
        if not self.active and value < self.enter:    # 0.25
            self.active = True
        elif self.active and value > self.exit:       # 0.40
            self.active = False
        return self.active

stable = self.pinch_debounce.update(raw_pinch, t_ms)  # 120 ms bekleme
if stable and not self.state.pinching:
    events.append("pinch_basladi")                    # yalnızca geçiş anında`,
    },
  },
  {
    id: "demo-el", section: "El", session: "3", minutes: 12, camera: true,
    title: "Canlı demo B: Pinch ile sürgü ve sürükleme",
    notes: [
      "Kamera başlatılır; işaret parmağı ucu imleç olur. Sürgünün tutamacı üzerinde pinch yapılıp sürüklenir; kutu da pinch ile taşınır.",
      "Pinch çubuğundaki giriş ve çıkış çizgileri histerezisi gösterir. Komut sayacı bir hareketin yalnızca bir komut ürettiğini doğrular.",
      "El kadrajdan çıkınca 'El kayboldu: durum sıfırlandı' görünür ve sürüklenen öğe bırakılır.",
      "İşletim sisteminin faresi kontrol edilmez; bütün etkileşim uygulamanın içindedir.",
    ],
    code: {
      file: "examples/08_el_jestleri.py", run: "python examples/08_el_jestleri.py",
      snippet: `cursor = canvas.screen(hand.points[8])          # işaret ucu, ekran koordinatı
state = controller.update(hand.points, frame.timestamp_ms, cursor)
started = "pinch_basladi" in state.events
slider.update(cursor, started, state.pinching)    # yalnızca pinch başında tutulur
box.update(cursor, started, state.pinching)`,
    },
  },
  {
    id: "bolgeler", section: "Cilt", session: "4", minutes: 8,
    title: "Cilt bölgesi çıkarma",
    notes: [
      "Katmanlar sırayla açılır: yüz ağı, alın ve yanak çokgenleri, göz/kaş/dudak dışlaması, kenardan içeri çekme ve saç maskesi.",
      "Bölge adları kişinin kendi sağına göredir; aynalanmamış görüntüde kişinin sağ yanağı solda görünür.",
      "Python uygulamasında saç ve aksesuarlar Selfie Multiclass segmentasyon modeliyle ayrılır; model yoksa koyu pikselleri atan renk tutarlılığı yöntemi kullanılır.",
    ],
    code: {
      file: "src/skin/regions.py", run: "python examples/09_cilt_bolgeleri.py",
      snippet: `raw[name] = cv2.erode(polygon_mask(points, idx, shape), kernel)  # kenardan içeri
raw[name][excl > 0] = 0                                         # göz, kaş, dudak
if seg_mask is not None:
    allowed = (seg_mask == SEG_FACE_SKIN).astype(np.uint8) * 255  # yalnızca yüz cildi
final = cv2.bitwise_and(raw[name], allowed)
coverage[name] = np.count_nonzero(final) / np.count_nonzero(raw[name])`,
    },
  },
  {
    id: "isik", section: "Cilt", session: "4", minutes: 8,
    title: "Işığın etkisi: cilt aynı, sayı farklı",
    notes: [
      "Sentetik cilt yaması sabittir; yalnızca ışığın rengi, şiddeti ve yönü değiştirilir.",
      "Sıcak ışıkta mutlak a* değeri belirgin biçimde artar; yan ışıkta iki yarı arasındaki renk farkı (ΔE) büyür. Cilt değişmemiştir.",
      "Bu yüzden farklı günlerde standart ışık ve kamera ayarları olmadan alınan ölçümler gerçek bir değişim gibi karşılaştırılmaz.",
      "Python uygulamasında bir fotoğrafın renkleri sıcak ışık yönünde kaydırıldığında alnın a* değeri 15,7'den 24,2'ye çıkmıştır.",
    ],
    code: {
      file: "src/skin/metrics.py", run: "python examples/10_cilt_analizi.py",
      snippet: `lab = lab_float(image_bgr)              # L* 0-100, a*, b*
median_a = np.median(a_star[union])     # yüzün kendi ortancası
redness = a_star - median_a             # göreli kızarıklık görünümü (Δa*)
# Mutlak a* ışığa ve kameraya bağlıdır; göreli değer daha az etkilenir ama sıfırlanmaz.`,
    },
  },
  {
    id: "demo-cilt", section: "Cilt", session: "4", minutes: 12, camera: true,
    title: "Canlı demo C: Kalite kontrolü ve açıklanabilir harita",
    notes: [
      "Kamera başlatılır, kişi önden ve iyi ışıkta durur, 'Kare al' düğmesine basılır. Analiz tek kare üzerinde yapılır.",
      "Kalite listesindeki bir satır kırmızıysa sonuç üretilmez ve neden yazılır: baş döndürülerek veya ortam karartılarak bu davranış gösterilir.",
      "Isı haritası yalnızca bölge maskesi içinde ve sabit aralıkla (Δa* -10 ile +10) renklendirilir. Uyarı metni her zaman görünür.",
      "Tarayıcı demosu saç ayrımı için renk tutarlılığı yöntemini kullanır; segmentasyon modeli Python uygulamasındadır. Görüntü kaydedilmez.",
    ],
    code: {
      file: "src/skin/analyzer.py", run: "python examples/10_cilt_analizi.py",
      snippet: `regions = build_region_masks(crop, points, 320, config.SKIN_ROI_EROSION_RATIO, seg)
quality = check_quality(crop, len(faces), width_full, face.pose, face_box, union,
                        regions.coverage)
if not quality.ok:
    return SkinReport(quality, None, crop, regions)   # sonuç üretilmez
metrics = compute_metrics(crop, valid_regions)`,
    },
  },
  {
    id: "model", section: "Cilt", session: "4", minutes: 8,
    title: "Kural tabanlı analiz ve öğrenilmiş model",
    notes: [
      "Üç kart aynı sentetik görüntü üzerinde sınıflandırma, tespit ve segmentasyonun farkını gösterir.",
      "Entegre edilen öğrenilmiş model Selfie Multiclass Segmenter'dır: her piksele sınıf verir, cildin durumu hakkında bir şey söylemez.",
      "acne-lds değerlendirilmiş ama entegre edilmemiştir: ağırlık lisansı belirsiz, veri akademik kullanımla sınırlı, klinik fotoğraflardan web kamerasına alan farkı var. Bir sınıflandırıcının çıktısına kutu çizmek modelin üretmediği bilgiyi uydurmaktır.",
      "Grad-CAM benzeri haritalar modelin dikkat ettiği bölgeyi kabaca gösterir; lezyon segmentasyonu değildir.",
    ],
    code: {
      file: "src/skin/segmenter.py", run: "python examples/09_cilt_bolgeleri.py",
      snippet: `options = vision.ImageSegmenterOptions(
    base_options=base_options(config.SEGMENTER_MODEL),
    running_mode=vision.RunningMode.IMAGE, output_category_mask=True)
mask = segmenter.segment(mp_image).category_mask.numpy_view()
# 0 arka plan, 1 saç, 2 vücut cildi, 3 yüz cildi, 4 giysi, 5 diğer`,
    },
  },
  {
    id: "kaynaklar-karsilastirma", section: "Proje", session: "4", minutes: 6,
    title: "GitHub kaynaklarının karşılaştırılması",
    notes: [
      "Satıra tıklandığında doğrulanan özellikler ve sınırlamalar açılır. Filtreler kullanılan, fikir alınan ve kullanılmayan kaynakları ayırır.",
      "Kod lisansı, model ağırlığı lisansı ve veri lisansı ayrı ayrı değerlendirilmiştir; herkese açık bir depo serbest kullanım izni anlamına gelmez.",
      "Yıldız sayısı kalite ölçütü değildir; kontrol tarihi 19.10.2026'dır. Ayrıntılı tablo öğrenci raporunun ekindedir.",
    ],
  },
  {
    id: "mimari", section: "Proje", session: "4", minutes: 8,
    title: "Birleşik mimari: tek kamera, ortak kare",
    notes: [
      "Mod düğmeleri hangi modüllerin çalıştığını değiştirir; cilt modülünün düşük sıklıkta çalıştığı ayrı renkle gösterilir.",
      "Bir modüle tıklandığında girdi, çıktı ve sorumluluğu görünür. Modül adları Python projesindeki klasörlerle aynıdır: camera, common, face, hands, skin.",
      "Eksik model yalnızca kendi modülünü kapatır; kamera her durumda with yapısıyla bırakılır.",
    ],
    code: {
      file: "src/main.py", run: "python src/main.py",
      snippet: `frame = prepare(raw)                         # bir kez küçült, bir kez RGB
if use_face:  face_res = face_mod.process(frame)
if use_hands: hand_res = hand_mod.process(frame)
state = gestures.update(points, frame.timestamp_ms, cursor)
if mode == "Cilt" and time.monotonic() - last_skin > 0.5:   # düşük sıklık
    skin_preview = skin_mod.analyze(frame.full_bgr, face_res.faces, frame.scale_to_full)`,
    },
  },
  {
    id: "gorevler", section: "Proje", session: "1-4", minutes: 5,
    title: "Öğrenci görevleri ve deneyler",
    notes: [
      "Her oturumun görevleri işaretlenebilir; işaretler yalnızca bu tarayıcıda saklanır.",
      "Deneylerin amacı ölçümün sınırını görmektir: ışık, mesafe, poz ve eşik değişikliklerinin sonuca etkisi not edilir.",
      "Performans tablosu için scripts/benchmark.py her öğrencinin bilgisayarında çalıştırılabilir.",
    ],
  },
  {
    id: "final", section: "Proje", session: "4", minutes: 10, camera: true,
    title: "Final demo: yüz ve el birlikte",
    notes: [
      "Kamera başlatılır. Yüz konturları ve el imleci aynı anda görünür; üstteki mod düğmeleri işaret parmağıyla üzerine gelinip pinch yapılarak değiştirilir.",
      "Bu, Python'daki src/main.py uygulamasının tarayıcıdaki sadeleştirilmiş eşidir. Python uygulaması: python src/main.py",
      "Her iki model aynı karede çalıştığı için panelde yüz ve el model süreleri ayrı ayrı görünür; bunlar tarayıcıda o an ölçülen değerlerdir.",
    ],
    code: {
      file: "src/main.py", run: "python src/main.py",
      snippet: `clicked = buttons.update(cursor, started)    # düğme üstünde pinch = tıklama
if clicked is not None:
    mode = MODES[clicked]                    # Yüz / El / Cilt / Birleşik`,
    },
  },
  {
    id: "sonraki", section: "Proje", session: "4", minutes: 4,
    title: "Kaynaklar ve sonraki adımlar",
    notes: [
      "Kaynaklar öğrenci raporunun N bölümünde tıklanabilir bağlantılarla yer alır.",
      "Proje geliştirme fikirleri arasından bir tanesi seçilip küçük bir deney raporu hazırlanabilir.",
      "İletişim ve depo bağlantısı workshop.config.json dosyasından gelir.",
    ],
  },
];

// Oturum akışı: [başlangıç, konu, dakika, sahne kimlikleri, Python dosyası]
// Her oturum 75 dk + 15 dk ara + 90 dk = 180 dk. Öğrenci raporundaki takvimle aynıdır.
export const SESSION_FLOW = [
  { session: "1", title: "Temeller", outcome: "Görüntüyü dizi olarak okuyup kural tabanlı bir işleme hattı kurmak", slots: [
    ["0:00", "Tanışma, gizlilik ve gönüllülük", 10, ["acilis", "rota"], ""],
    ["0:10", "Kurulum kontrolü", 20, [], "scripts/check_setup.py --kamera"],
    ["0:30", "Kamera döngüsü ve FPS", 20, ["veri"], "examples/01_kamera.py"],
    ["0:50", "NumPy dizisi, BGR/RGB, gri, HSV, LAB", 25, ["renk"], "examples/02_piksel_renk.py"],
    ["1:15", "Ara", 15, [], ""],
    ["1:30", "ROI ve yeniden boyutlandırma", 20, ["roi"], "examples/03_filtre_esik.py"],
    ["1:50", "Gaussian bulanıklık, eşik, Otsu", 25, ["roi", "esik"], "examples/03_filtre_esik.py"],
    ["2:15", "Morfoloji ve kontur", 20, ["esik"], "examples/03_filtre_esik.py"],
    ["2:35", "FPS, gecikme; kural tabanlı ve öğrenilmiş yöntem", 15, ["veri"], ""],
    ["2:50", "Öğrenci deneyi ve kapanış", 10, ["gorevler"], ""],
  ] },
  { session: "2", title: "Yüz", outcome: "Noktalardan mesafeden bağımsız ölçüm üretmek ve ölçümün sınırını tanımak", slots: [
    ["0:00", "Tekrar", 10, [], ""],
    ["0:10", "OpenCV ve MediaPipe'ın rolleri, Tasks API", 15, ["roller"], ""],
    ["0:25", "Yüz tespiti, kutu, noktalar, Haar karşılaştırması", 25, ["takip", "demo-yuz"], "examples/04_yuz_tespiti.py"],
    ["0:50", "Takip ve tanıma farkı, hareket izi, EMA", 25, ["takip", "iz"], "examples/05_yuz_takip.py"],
    ["1:15", "Ara", 15, [], ""],
    ["1:30", "Aynalama, koordinatlar, normalize ölçüm", 20, ["normalize"], ""],
    ["1:50", "EAR, ağız açıklığı, baş yönelimi, blendshape", 30, ["demo-yuz"], "examples/06_yuz_geometrisi.py"],
    ["2:20", "Yüz oranları, sınırları, \"Bir kamera neyi ölçebilir?\"", 20, ["geometri"], "examples/06_yuz_geometrisi.py"],
    ["2:40", "Mesafe ve poz deneyi", 20, ["geometri", "gorevler"], "examples/06_yuz_geometrisi.py"],
  ] },
  { session: "3", title: "El", outcome: "Gürültülü model çıktısından güvenilir komut üretmek", slots: [
    ["0:00", "Tekrar", 10, [], ""],
    ["0:10", "21 el noktası, eklem açıları, parmak durumları", 25, ["el"], "examples/07_el_noktalari.py"],
    ["0:35", "Sağ/sol etiketi ve aynalama deneyi", 15, ["el"], "examples/07_el_noktalari.py"],
    ["0:50", "Pinch ve normalize mesafe", 25, ["kararlilik"], "examples/08_el_jestleri.py"],
    ["1:15", "Ara", 15, [], ""],
    ["1:30", "Histerezis, bekleme ve soğuma süresi, el kaybında sıfırlama", 30, ["kararlilik"], "src/hands/gestures.py"],
    ["2:00", "Sürgü, sürükleme ve çizim", 35, ["demo-el"], "examples/08_el_jestleri.py"],
    ["2:35", "Tek komut testi ve eşik ayarı", 25, ["gorevler"], "src/config.py"],
  ] },
  { session: "4", title: "Cilt ve birleşik uygulama", outcome: "Kaliteye bağlı, açıklanabilir ve sınırları belirtilmiş analiz yapmak", slots: [
    ["0:00", "Tekrar", 10, [], ""],
    ["0:10", "Cilt bölgeleri, dışarıda bırakma, segmentasyon modeli", 25, ["bolgeler"], "examples/09_cilt_bolgeleri.py"],
    ["0:35", "Görüntü kalite kontrolü", 20, ["demo-cilt"], "examples/10_cilt_analizi.py"],
    ["0:55", "Görünüm göstergeleri ve ısı haritaları", 20, ["demo-cilt"], "examples/10_cilt_analizi.py"],
    ["1:15", "Ara", 15, [], ""],
    ["1:30", "Işığın etkisi deneyi", 20, ["isik"], "examples/10_cilt_analizi.py"],
    ["1:50", "Kural tabanlı analiz ve öğrenilmiş model; açık kaynak model değerlendirmesi", 20, ["model", "kaynaklar-karsilastirma"], ""],
    ["2:10", "Birleşik uygulama ve mimari", 30, ["mimari", "final"], "src/main.py"],
    ["2:40", "Final demo ve sonraki adımlar", 20, ["final", "sonraki"], "src/main.py"],
  ] },
];
