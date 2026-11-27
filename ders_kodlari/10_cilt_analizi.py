"""10 - Açıklanabilir cilt görünümü analizi (tek kare)

Öğrenme hedefi: Kalite kontrolünden geçen tek bir kareden açıklanabilir
göstergeler ve ısı haritaları üretmek; kalite yetersizse sonuç üretmemek.

Çalıştırma : python examples/10_cilt_analizi.py
Otomatik   : python examples/10_cilt_analizi.py --otomatik
Kullanım   : boşluk: analiz için kare al | 1-4: harita seç | f: özellikler | q: çıkış

Eğitim amaçlı görüntü analizi; tıbbi tanı değildir. Görüntüler kaydedilmez.
"""

import _yol  # noqa: F401

import time

import numpy as np

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import status_line
from common.frame import FramePreparer
from common.models import ModelMissingError
from face.tracker import FaceTracker
from skin.analyzer import SkinAnalyzer
from skin.overlay import MAP_KEYS, disclaimer, draw_quality, result_panel

PREVIEW_INTERVAL_S = 0.5     # kalite önizlemesinin güncellenme aralığı

HELP_LINES = [
    "Amaç: Işık, poz ve netlik kalite kontrolünden geçen tek kareden açıklanabilir cilt ısı haritası üretmek.",
    "• [Boşluk / Space] Soldaki 6 kalite göstergesi yeşil olunca tek kare analiz alır.",
    "• [1] Kızarıklık (Δa*)  ·  [2] Parlama  ·  [3] Doku  ·  [4] Renk farkı (ΔE) haritaları.",
    "• İki yanak arasındaki ΔE farkı genellikle ışığın tek taraftan gelmesinden kaynaklanır.",
    "• Etik Not: Yalnızca eğitim amaçlı görüntü analizidir; tıbbi tanı değildir.",
]


def main():
    parser = build_parser("Cilt görünümü analizi")
    parser.add_argument("--otomatik", action="store_true",
                        help="Kalite uygun olduğunda birkaç saniyede bir otomatik analiz yap.")
    parser.add_argument("--segmentasyonsuz", action="store_true", help="Segmentasyon modelini kullanma.")
    args = parser.parse_args()
    prepare = FramePreparer(config.PROCESS_WIDTH)
    analyzer = SkinAnalyzer(use_segmenter=not args.segmentasyonsuz)
    print(analyzer.segmenter_note)
    preview, captured, map_name = None, None, MAP_KEYS[0]
    last_preview = last_auto = 0.0

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            FaceTracker() as faces, \
            DisplayLoop(
                "VISION LAB - 10 Cilt analizi",
                args,
                help_title="10 · Açıklanabilir Cilt Görünümü Analizi",
                help_lines=HELP_LINES,
            ) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            result = faces.process(frame)
            now = time.monotonic()

            # Kalite önizlemesi düşük sıklıkta çalışır; yüz takibi her karede devam eder.
            if now - last_preview >= PREVIEW_INTERVAL_S:
                preview = analyzer.analyze(frame.full_bgr, result.faces, frame.scale_to_full)
                last_preview = now
                if args.otomatik and preview.metrics is not None and \
                        now - last_auto >= config.AUTO_ANALYSIS_INTERVAL_S:
                    captured, last_auto = preview, now

            # 820px genişlik: 16:9 kamerada ~461px yükseklik -> sağ panel hiç taşmaz
            canvas = Canvas(frame, width=820, mirror=not args.no_mirror)
            canvas.flip()
            img = canvas.image
            disclaimer(img)
            if preview is not None:
                draw_quality(img, preview.quality, 12, 38)
            hint = "Boşluk: analiz al  ·  1-4: harita  ·  [F] Özellikler" if preview is not None and preview.quality.ok else \
                ("Uygun görüntü bekleniyor: " + (preview.quality.first_problem if preview else ""))
            status_line(img, hint, "ok" if preview is not None and preview.quality.ok else "warn")

            side = result_panel(captured, map_name, height=img.shape[0], width=430)
            key = loop.show(np.hstack([img, side]))
            if key == ord(" "):
                captured = analyzer.analyze(frame.full_bgr, result.faces, frame.scale_to_full)
                print(captured.message, f"({captured.elapsed_ms:.0f} ms)")
            elif ord("1") <= key <= ord("4"):
                map_name = MAP_KEYS[key - ord("1")]
    analyzer.close()


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
