"""09 - Cilt analiz bölgelerinin çıkarılması

Öğrenme hedefi: Yüz noktalarından alın ve yanak maskeleri oluşturmak; göz, kaş
ve dudakları dışarıda bırakmak; saçı segmentasyon modeliyle ayırmak.

Çalıştırma : python examples/09_cilt_bolgeleri.py
Kullanım   : s: segmentasyon modelini aç/kapat (karşılaştırma için)   q: çıkış
"""

import _yol  # noqa: F401

import config
from camera import Camera, CameraError
from common.app import Canvas, DisplayLoop, build_parser
from common.draw import GRAY, WHITE, panel, put_text, status_line
from common.frame import FramePreparer
from common.models import ModelMissingError
from face.tracker import FaceTracker
from skin.overlay import REGION_COLORS, disclaimer, draw_regions
from skin.regions import build_region_masks


def main():
    args = build_parser("Cilt analiz bölgeleri").parse_args()
    prepare = FramePreparer(config.PROCESS_WIDTH)
    segmenter, use_seg = None, False
    try:
        from skin.segmenter import SkinSegmenter
        segmenter, use_seg = SkinSegmenter(), True
    except ModelMissingError as exc:
        print(f"Segmentasyon olmadan devam ediliyor: {exc}")

    with Camera(args.source, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT) as cam, \
            FaceTracker() as faces, DisplayLoop(
                "VISION LAB - 09 Cilt bolgeleri",
                args,
                help_title="09 · Cilt Analiz Bölgeleri & Saç/Göz Dışlama",
                help_lines=[
                    "Amaç: Yüz noktalarından alın ve yanak maskeleri çıkarmak; göz, dudak ve saçı dışarıda bırakmak.",
                    "• [s] Segmentasyon (saç/arka plan ayırma) modelini aç/kapat ve kalan alan yüzdesini kıyasla.",
                    "• Koyu alanlar analize dahil edilmeyen (dışlanan) bölgelerdir.",
                    "• [F] Bu rehberi aç/kapat  ·  [Q / Esc] Çıkış.",
                ],
            ) as loop:
        while loop.running:
            raw = cam.read()
            if raw is None:
                break
            frame = prepare(raw)
            result = faces.process(frame)
            canvas = Canvas(frame, mirror=not args.no_mirror)
            regions = None
            if len(result.faces) == 1:
                face = result.faces[0]
                seg = segmenter.segment(canvas.image) if (use_seg and segmenter) else None
                regions = build_region_masks(canvas.image, canvas.pts(face.points), face.width_px * canvas.scale,
                                             config.SKIN_ROI_EROSION_RATIO, seg)
                draw_regions(canvas.image, regions)
            canvas.flip()
            img = canvas.image
            disclaimer(img)
            if regions:
                panel(img, 12, 40, 300, 186)
                put_text(img, f"yöntem: {regions.method}", (24, 48), 15, WHITE)
                for i, (name, frac) in enumerate(regions.coverage.items()):
                    put_text(img, f"{name}: kalan alan %{frac * 100:.0f}", (24, 76 + 26 * i), 15, REGION_COLORS[name])
                put_text(img, "koyu alanlar: dışarıda bırakılan", (24, 160), 13, GRAY)
                status_line(img, "1 yüz: bölgeler çıkarıldı", "ok")
            else:
                status_line(img, "Tek bir yüz bekleniyor." if result.faces else result.status, "warn")
            if loop.show(img) == ord("s") and segmenter:
                use_seg = not use_seg
    if segmenter:
        segmenter.close()


if __name__ == "__main__":
    try:
        main()
    except (CameraError, ModelMissingError) as exc:
        print(exc)
