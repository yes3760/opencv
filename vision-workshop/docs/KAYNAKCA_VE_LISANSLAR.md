# Kaynakça ve üçüncü taraf lisans notları

Kontrol tarihi: 19 Ekim 2026. Kod lisansı, model ağırlığı lisansı ve veri kümesi lisansı ayrı ayrı
değerlendirilmiştir. Bir deponun herkese açık olması, kodunun veya ağırlıklarının serbestçe
kullanılabileceği anlamına gelmez.

## Bu projenin kendi lisansı

Proje kodu ve eğitim materyali için lisans topluluk tarafından seçilecektir; depoda henüz `LICENSE`
dosyası yoktur. Aşağıdaki bağımlılıklarla uyumlu seçenekler MIT veya Apache-2.0'dır. Lisans
seçilmeden önce materyal yalnızca eğitim içinde kullanılmalıdır.

## Kullanılan yazılım bileşenleri

| Bileşen | Sürüm | Lisans | Kaynak | Not |
|---|---|---|---|---|
| OpenCV (`opencv-contrib-python`) | 4.14.0.94 | Apache-2.0 | <https://github.com/opencv/opencv> | Yerleşik Haar XML dosyaları dosya başlığında "Intel License Agreement" (BSD benzeri) taşır |
| MediaPipe | 1.1.1 (Intel Mac: 0.10.21) | Apache-2.0 | <https://github.com/google-ai-edge/mediapipe> | |
| NumPy | 2.x | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | <https://numpy.org> | PyPI kaydındaki lisans ifadesi |
| Pillow | 10 ve üstü | MIT-CMU | <https://python-pillow.org> | Türkçe karakterli yazı çizimi |
| matplotlib, absl-py, flatbuffers, sounddevice, certifi | MediaPipe bağımlılıkları | matplotlib lisansı, Apache-2.0, Apache-2.0, MIT, MPL-2.0 | PyPI | Doğrudan kullanılmaz (matplotlib yalnızca rapor şekillerinde) |
| `@mediapipe/tasks-vision` | 1.1.1 | Apache-2.0 | <https://www.npmjs.com/package/@mediapipe/tasks-vision> | Sunumdaki canlı demolar; wasm dosyaları yerelden sunulur |
| React, React DOM | 19.3.0 | MIT | <https://react.dev> | Sunum |
| Vite, @vitejs/plugin-react | 8.3.2, 6.1.1 | MIT | <https://vite.dev> | Geliştirme ve derleme |
| TypeScript | 7.0.2 | Apache-2.0 | <https://www.typescriptlang.org> | Tip denetimi |
| Inter, Space Grotesk, JetBrains Mono (@fontsource) | 5.3.0 | SIL Open Font License 1.1 | <https://fontsource.org> | Sunum yazı tipleri, yerelden sunulur |

## Model dosyaları

| Model | Dosya | Lisans (model kartı) | Kaynak | Eğitim verisi |
|---|---|---|---|---|
| Face Landmarker (BlazeFace + Face Mesh V2 + Blendshape) | `face_landmarker.task` (3,8 MB) | Apache-2.0 | <https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker> | Yayımlanmamış; model kartında akıllı telefon kameralarıyla toplanmış, onaylı görüntüler |
| Hand Landmarker | `hand_landmarker.task` (7,8 MB) | Apache-2.0 | <https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker> | Yayımlanmamış; yaklaşık 30 bin gerçek ve sentetik görüntü (belge) |
| Selfie Multiclass Segmenter 256×256 | `selfie_multiclass_256x256.tflite` (16,4 MB) | Apache-2.0 | <https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter> | Yayımlanmamış |
| Standart yüz modeli | `shared/canonical_face_478.json` | Apache-2.0 | MediaPipe deposu, `mediapipe/modules/face_geometry/data/face_model_with_iris.obj` | — |

Model kartları:

- Face Mesh V2: <https://storage.googleapis.com/mediapipe-assets/Model%20Card%20MediaPipe%20Face%20Mesh%20V2.pdf>
- BlazeFace (Short Range): <https://storage.googleapis.com/mediapipe-assets/MediaPipe%20BlazeFace%20Model%20Card%20(Short%20Range).pdf>
- Blendshape V2: <https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Blendshape%20V2.pdf>
- Hand Tracking: <https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Hand%20Tracking%20(Lite_Full)%20with%20Fairness%20Oct%202021.pdf>
- Multiclass Segmentation: <https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Multiclass%20Segmentation.pdf>

Bütün model kartları insan hayatını etkileyen kararları, gözetimi ve kimlik tanımayı kapsam dışı
sayar. Bu proje kimlik tanıma yapmaz.

## İncelenen ancak kullanılmayan veya yalnızca fikir alınan kaynaklar

| Kaynak | Kod lisansı | Model / veri | Bu projedeki durumu |
|---|---|---|---|
| [DurtyDhiana/skin-scan](https://github.com/DurtyDhiana/skin-scan) | MIT | Ağırlık yok | Renk uzayı yöntemleri fikir olarak alındı; kod kopyalanmadı, adlandırma değiştirildi |
| [Corerishi/VitalGaze](https://github.com/Corerishi/VitalGaze) | Lisans dosyası yok | Kaynağı belirsiz pickle modeli | Kullanılmadı |
| [openface-io/acne-lds](https://github.com/openface-io/acne-lds) | MIT | Ağırlık lisansı belirtilmemiş; ACNE04 "yalnızca akademik kullanım" | Değerlendirildi, entegre edilmedi; ağırlıklar indirilmedi |
| [xpwu95/LDL](https://github.com/xpwu95/LDL) (ACNE04) | Lisans dosyası yok | "free for academic usage" ifadesi | Yalnızca veri koşulları incelendi |
| [cvzone/cvzone](https://github.com/cvzone/cvzone) | MIT | MediaPipe modelleri | Güncel MediaPipe ile uyumsuz; kullanılmadı |
| [opencv/opencv_zoo](https://github.com/opencv/opencv_zoo) YuNet | Apache-2.0 | Model: MIT | Alternatif olarak anıldı; kullanılmadı |
| [google-ai-edge/mediapipe-samples](https://github.com/google-ai-edge/mediapipe-samples) | Apache-2.0 | Örnek görsellerin lisansı belirtilmemiş | API başvurusu; kod ve görseller dağıtılmadı |
| Hugging Face cilt modelleri (charuka0/acne-multilabel-classifier, mufasabrownie/glowlytics-skin-models) | Model kartında MIT | Kaggle verisi; UTKFace ve FFHQ ticari olmayan kullanım koşulları | Kullanılmadı |

## Görseller ve örnek medya

- Rapor şekilleri gerçek kişi görüntüsü içermez: yüz şekilleri standart yüz modelinden, grafikler
  sentetik sinyallerden üretilmiştir (`docs/tools/make_figures.py`).
- Sunumdaki örnek gösterimler sentetiktir ve ekranda "Örnek gösterim" olarak etiketlenir.
- Doğrulama sırasında MediaPipe'ın resmî örnek görselleri (`storage.googleapis.com/mediapipe-assets`)
  yalnızca yerel test için kullanılmış, projeye eklenmemiştir.

## Bilimsel kaynaklar

Tam kaynak listesi öğrenci raporunun N bölümündedir: OpenCV (Bradski, 2000), MediaPipe (Lugaresi
vd., 2019), BlazeFace (Bazarevsky vd., 2019), Face Mesh (Kartynnik vd., 2019), MediaPipe Hands
(Zhang vd., 2020), Viola ve Jones (2001), Otsu (1979), Soukupová ve Čech (2016), Casiez vd. (2012),
Pech-Pacheco vd. (2000), Selvaraju vd. (2017), Barrett vd. (2019), Buolamwini ve Gebru (2018),
Mitchell vd. (2019), Prokhorov ve Kalinin (2024), Wu vd. (2019).
