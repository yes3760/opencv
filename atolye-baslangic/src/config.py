"""VISION LAB uygulamasının ayarları ve eşikleri.

Bu dosya, projedeki tüm eşiklerin tek kaynağıdır. Her değerin yanında
nereden geldiği belirtilmiştir:

  [Belge]  Resmî dokümantasyondaki varsayılan değer.
  [Kaynak] Yayımlanmış bir çalışmada önerilen yöntem veya değer.
  [Deney]  Bu eğitim için örnek görüntülerle seçilmiş başlangıç değeri.
           Kendi kameranızda deneyerek ayarlamanız beklenir.

Tarayıcı sunumundaki karşılıkları presentation/src/lib/config.ts dosyasındadır;
tests/test_config_sync.py iki dosyanın ortak değerlerinin aynı kaldığını denetler.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "models"

# ---------------------------------------------------------------------------
# Kamera ve kare boyutu
# ---------------------------------------------------------------------------
CAMERA_INDEX = "auto"       # "auto": siyah olmayan görüntü veren ilk kamera seçilir.
                            # 0 numara her zaman dahili kamera değildir (ör. Mac'te
                            # iPhone Süreklilik Kamerası 0 olabilir). Elle: 0, 1, 2...
CAPTURE_WIDTH = 1280        # Kameradan istenen çözünürlük. Kamera desteklemezse
CAPTURE_HEIGHT = 720        # en yakın değeri verir; gerçek değer ekranda yazar.
PROCESS_WIDTH = 480         # [Deney] Modellere verilen karenin genişliği (480px:
                            # MediaPipe 192-256px'e küçülttüğü için aynı doğrulukta ~%45 daha hızlı).
DISPLAY_WIDTH = 880         # Pencerede gösterilen görüntünün genişliği (yan panelle
                            # birlikte 1280 piksel genişliğindeki ekranlara sığar)
MIRROR_DISPLAY = True       # Ekran ayna gibi gösterilir; modeller ise aynalanmamış
                            # kareyi görür (bkz. rapor, "Aynalama" bölümü).

# ---------------------------------------------------------------------------
# Model dosyaları (scripts/download_models.py ile indirilir)
# ---------------------------------------------------------------------------
FACE_MODEL = MODEL_DIR / "face_landmarker.task"
HAND_MODEL = MODEL_DIR / "hand_landmarker.task"
SEGMENTER_MODEL = MODEL_DIR / "selfie_multiclass_256x256.tflite"

# ---------------------------------------------------------------------------
# Yüz modülü
# ---------------------------------------------------------------------------
MAX_FACES = 1                        # [Belge] num_faces. MediaPipe'ın kendi
                                     # yumuşatması yalnızca 1 yüzde uygulanır.
MIN_FACE_DETECTION_CONFIDENCE = 0.5  # [Belge] varsayılan
MIN_FACE_PRESENCE_CONFIDENCE = 0.5   # [Belge] varsayılan
MIN_TRACKING_CONFIDENCE = 0.5        # [Belge] varsayılan

TRAIL_LENGTH = 45                    # [Deney] Hareket izinde tutulan nokta sayısı
EMA_ALPHA = 0.35                     # [Deney] Üstel hareketli ortalama katsayısı.
                                     # 1'e yaklaştıkça hızlı ama titrek, 0'a
                                     # yaklaştıkça yumuşak ama gecikmeli.
TRACK_MATCH_MAX_DIST = 0.6           # [Deney] Takip numarası eşleştirmesi için en
                                     # fazla merkez kayması (yüz genişliği oranı)
FACE_LOST_RESET_FRAMES = 15          # [Deney] Bu kadar kare yüz yoksa iz silinir.

EYE_CLOSED_EAR = 0.20                # [Kaynak] Soukupová ve Čech (2016) göz en-boy
                                     # oranı (EAR) için 0.2 civarını kullanır. Örnek
                                     # görüntülerde açık gözde 0,20-0,32 ölçüldüğü için
                                     # yalnızca başvuru değeri olarak tutulur.
EYE_CLOSED_RATIO = 0.65              # [Deney] EAR, kişinin son karelerdeki ortancasının
                                     # bu oranının altına inerse göz kapalı sayılır.
MOUTH_OPEN_MAR = 0.35                # [Deney] İç dudak açıklığı / ağız genişliği

FRONTAL_MAX_YAW_DEG = 15.0           # [Deney] Önden poz kabul sınırları. Örnek
FRONTAL_MAX_PITCH_DEG = 20.0         # görüntülerde kameraya bakan yüzlerde bile
FRONTAL_MAX_ROLL_DEG = 12.0          # 5-18 derece eğim ölçüldüğü için geniş tutuldu.
MIN_FACE_WIDTH_RATIO = 0.18          # [Deney] Yüz genişliği / kare genişliği
SHAPE_STABLE_FRAMES = 20             # [Deney] Şekil eğilimi göstermeden önce
                                     # oranların kararlı kalması gereken kare sayısı
SHAPE_MAX_RATIO_STD = 0.02           # [Deney] Bu karelerde oranın en fazla sapması

# ---------------------------------------------------------------------------
# El modülü
# ---------------------------------------------------------------------------
MAX_HANDS = 1                        # Etkileşim için tek el yeterli ve daha kararlı.
MIN_HAND_DETECTION_CONFIDENCE = 0.5  # [Belge] varsayılan
MIN_HAND_PRESENCE_CONFIDENCE = 0.5   # [Belge] varsayılan
HAND_TRACKING_CONFIDENCE = 0.5       # [Belge] varsayılan

PINCH_ENTER_RATIO = 0.25             # [Deney] Başparmak-işaret ucu mesafesi / avuç
PINCH_EXIT_RATIO = 0.40              # boyu. Giriş ve çıkış eşiğinin farklı olması
                                     # histerezistir: sınırda titreşimi engeller.
                                     # Örneklerde açık elde 0,39-1,06 ölçüldü.
FINGER_EXTENDED_DEG = 150.0          # [Deney] Orta eklem (PIP) açısı bunun üstündeyse
FINGER_FOLDED_DEG = 120.0            # açık, altındaysa kapalı; arası belirsiz. Örneklerde
                                     # açık parmakta 163-180, kapalıda 5-80 derece ölçüldü.
THUMB_EXTENDED_DEG = 145.0           # [Deney] Başparmağın MCP ve IP açıları bunun üstündeyse açık
THUMB_FOLDED_DEG = 135.0             # [Deney] MCP veya IP açısı bunun altındaysa kapalı
GESTURE_STABLE_MS = 120              # [Deney] Jest bu süre değişmeden kalınca kabul edilir
COMMAND_COOLDOWN_MS = 700            # [Deney] İki komut arasındaki en kısa süre
HAND_LOST_RESET_MS = 300             # [Deney] El bu süre görünmezse durum sıfırlanır
OPEN_PALM_HOLD_MS = 1000             # [Deney] Açık el bu süre tutulursa çizim temizlenir
HANDEDNESS_SWAP = False              # Sağ/sol etiketi ters görünüyorsa True yapın
                                     # (bkz. 07_el_noktalari.py içindeki deney).

# ---------------------------------------------------------------------------
# Cilt görünümü modülü
# ---------------------------------------------------------------------------
SKIN_MIN_FACE_WIDTH_PX = 180         # [Deney] Analiz karesinde en küçük yüz genişliği.
                                     # Analiz 320 piksel yüz genişliğinde yapıldığı için
                                     # daha küçük yüzler aşırı büyütülmüş olur.
SKIN_MAX_YAW_DEG = 12.0              # [Deney] Cilt analizi için daha sıkı poz sınırı
SKIN_MAX_PITCH_DEG = 20.0
SKIN_MAX_ROLL_DEG = 10.0
SKIN_MIN_SHARPNESS = 20.0            # [Kaynak] Laplace varyansı bir netlik ölçüsüdür
                                     # (Pech-Pacheco vd., 2000). Burada gri tonların
                                     # varyansına bölünür (x1000); böylece karanlık veya
                                     # düşük kontrastlı görüntüler bulanık sanılmaz.
                                     # Eşik [Deney]: örneklerde net 62-305, 1 piksel
                                     # bulanıklıkta 9-18, 2 pikselde 2-5 ölçüldü.
SKIN_MIN_MEDIAN_L = 50               # [Deney] Bölge parlaklık ortancası (0-255) alt sınırı.
                                     # Koyu cilt tonlarında normal ışıkta da L düşük
                                     # olabileceği için sınır bilerek düşük tutuldu.
SKIN_MAX_MEDIAN_L = 235              # [Deney] üst sınırı
SKIN_MAX_CLIPPED_FRACTION = 0.08     # [Deney] Doymuş (L>=250) piksel oranı üst sınırı
SKIN_MAX_DARK_FRACTION = 0.10        # [Deney] Çok karanlık (L<=25) piksel oranı üst sınırı
SKIN_ROI_EROSION_RATIO = 0.015       # [Deney] Bölge kenarlarından içeri çekme (yüz genişliği oranı)
SKIN_MIN_VALID_FRACTION = 0.5        # [Deney] Maskeden sonra bölgede kalması gereken en az oran
SPECULAR_DELTA_L = 25                # [Deney] Parlama pikseli: bölgedeki ortancadan en az
                                     # bu kadar daha açık (L, 0-255) ve
SPECULAR_CHROMA_RATIO = 0.7          # [Deney] renk doygunluğu ortancanın bu oranından az.
                                     # Yansıyan ışık cildin rengini değil ışığın rengini
                                     # taşıdığı için daha açık ve daha soluk görünür.
                                     # Mutlak eşik (ör. L>225) açık tenli kişilerde ve
                                     # parlak ortamda bütün yüzü "parlak" sayıyordu.
TEXTURE_BLUR_SIGMA = 3.0             # [Deney] Doku için aydınlatmayı ayıran bulanıklık
SKIN_ANALYSIS_FACE_WIDTH = 320       # [Deney] Doku ölçümünden önce yüz bu genişliğe
                                     # ölçeklenir; böylece mesafe etkisi azalır.
AUTO_ANALYSIS_INTERVAL_S = 2.0       # Otomatik modda iki analiz arası süre
SKIN_DISCLAIMER = "Eğitim amaçlı görüntü analizi; tıbbi tanı değildir."

# ---------------------------------------------------------------------------
# Kayıt ve gizlilik
# ---------------------------------------------------------------------------
ALLOW_SAVE_DEFAULT = False           # Görüntüler varsayılan olarak kaydedilmez.
