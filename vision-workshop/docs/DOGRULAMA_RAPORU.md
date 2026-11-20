# Doğrulama raporu

İlk doğrulama 19.10.2026, güncelleme 24.10.2026. Ortam: Apple M4 MacBook Air, macOS 27.0.1,
Python 3.12.15, Node 22.17. Windows'ta çalıştırılmadı.

## Doğrulananlar

| Konu | Sonuç |
|---|---|
| Canlı kamera (Python) | `src/main.py` dahili kamerayla açıldı; kamera görüntüsü ve yüz noktaları ekranda görüldü (24.10.2026, kullanıcı onayıyla) |
| Canlı kamera (tarayıcı) | Sunumun 9. sahnesinde (canlı yüz demosu) varsayılan tarayıcıda kamera görüntüsü ve yüz noktaları görüldü (24.10.2026, kullanıcı onayıyla) |
| Birden fazla kamera | Bu Mac'te 0 numaralı kamera (iPhone Süreklilik Kamerası olduğu düşünülen) tamamen siyah kare verdi, 1 numara görüntü verdi. Varsayılan `--source auto` görüntü veren kamerayı (1) seçti |
| macOS kamera izni | İlk çalıştırmada OpenCV izni isteyip beklemeden hata verdi; uygulama artık izin için 20 saniye bekliyor ve izin sonrası açılıyor |
| Python testleri | 38 test geçti, 1 test örnek görsel klasörü verilmediği için atlandı (24.10.2026). İlk turda 36 test üç yapılandırmada geçmişti: mediapipe 1.1.1 + OpenCV 4.14.0.94; mediapipe 1.1.1 + OpenCV 5.0.0.93; mediapipe 0.10.21 + OpenCV 4.11 + NumPy 1.26 |
| Python ve sunum eşikleri | `tests/test_config_sync.py`: 28 sayısal eşik, uyarı metni ve yüz bölgesi noktaları iki tarafta aynı |
| Örnekler 01-10 ve `src/main.py` | Örnek görsel ve sentetik videolarla gerçek OpenCV penceresinde hatasız çalıştı |
| Model indirme | Temiz indirme, SHA-256 doğrulama ve bozuk dosyanın yeniden indirilmesi çalıştı |
| Eksik model | Yalnızca ilgili modül kapandı, uygulama devam etti |
| Kalite kontrolü | Bulanık, karanlık, aşırı parlak, küçük yüz varyantlarında cilt sonucu üretilmedi |
| Süre ölçümü | `scripts/benchmark.py`: yüz 5,9 ms, el 5,4 ms, cilt 37 ms (M4, 640 px). Canlı uygulamada pencerede 26 FPS görüldü |
| Rapor PDF | 18 sayfa; Türkçe karakterler, tablolar, kod blokları ve yatay ek sayfası görsel olarak kontrol edildi |
| Web sunumu derlemesi | `tsc --noEmit` ve `vite build` geçti |
| Sunum sahneleri | 24 sahnenin tamamı 1440×900 görünümde ekran görüntüsüyle kontrol edildi; taşan paneller (6, 18, 20) ve sentetik el (13) düzeltildi |
| Klavye | Sağ/sol ok, Home, End, F (odak modu), Esc, N (notlar), M (menü) çalıştı; sürgü odaktayken ok tuşu sahneyi değiştirmedi |
| Dokunmatik | Yapay dokunma olaylarıyla iki yönde kaydırma çalıştı; sürgü ve etkileşimli tuvallerde devre dışı |
| Kamera kaynak yönetimi | Sahte kamera akışıyla: sahne değişince ve "Kamerayı durdur" düğmesiyle akış gerçekten kapandı (`readyState = ended`) |
| Kamera seçici | Sahte iki kamerayla: liste göründü, seçilen kamera `deviceId` ile açıldı, önceki akış kapandı |
| Kamera hata ekranları | İzin reddi, cihaz yok, kamera meşgul, güvenli olmayan bağlam taklit edilerek doğru mesajlar görüldü |
| Tarayıcıda cilt analizi | Sentetik yüz görüntüsünde bütün kalite kontrolleri geçti; yanaklara eklenen kızarıklık Δa* = +2,6, alın 0, yanaklar arası ΔE 0,0 ölçüldü (245 ms) |
| Video dosyası kaynağı | Dosya seçimi ve model yüklenmesi çalıştı |
| Eğitmen notları | `npm run notes` ile sahne verisinden üretildi; dört oturumun her biri 180 dk, bütün sahne bağlantıları geçerli |

## Doğrulanamayanlar

- **Tarayıcıda diğer canlı demolar:** Yüz demosu (9) gerçek kamerayla doğrulandı. El (15), cilt (18) ve
  final (23) demoları ile "görüntü siyah" uyarısı gerçek kamerayla ayrıca denenmedi.
- **Hareket azaltma tercihi:** CSS ve JavaScript kodu yazıldı, ancak işletim sisteminde
  "hareketi azalt" açıkken denenmedi.
- **Python'da el ve cilt modları canlı kamerayla:** Kullanıcı yüz noktalarını doğruladı; el jestleri ve
  cilt analizi canlı kamerayla ayrıca kontrol edilmedi.
- **Windows ve Intel Mac donanımı:** Kurulum adımları paket kayıtlarına göre yazıldı, bu
  donanımlarda çalıştırılmadı.
- **acne-lds:** Ağırlıklar indirilmedi; entegrasyon yapılmadı.
