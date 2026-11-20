"""Python uygulaması ile web sunumunun aynı eşikleri ve aynı yüz bölgelerini kullandığını denetler.

Sunumdaki değerler presentation/src/lib/config.ts ve faceRegions.ts dosyalarındadır. Bir eşik
yalnızca bir tarafta değiştirilirse bu test başarısız olur.
"""

import re
from pathlib import Path

import pytest

import config
from face import metrics
from skin import regions

ROOT = Path(__file__).resolve().parents[1]
WEB_LIB = ROOT / "presentation" / "src" / "lib"

pytestmark = pytest.mark.skipif(not WEB_LIB.exists(), reason="sunum klasörü yok")


def ts_constants(path: Path) -> dict[str, str]:
    """`export const AD = değer;` satırlarını ham metin olarak okur."""
    text = path.read_text(encoding="utf-8")
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"export const (\w+)(?:\s*:\s*[^=]+)?\s*=\s*(\"[^\"]*\"|[^;]+);", text)}


def test_numeric_thresholds_match():
    web = ts_constants(WEB_LIB / "config.ts")
    numeric = {k: v for k, v in web.items() if re.fullmatch(r"-?\d+(\.\d+)?", v)}
    assert len(numeric) >= 20, "config.ts içinde beklenen eşikler bulunamadı"
    for name, value in numeric.items():
        assert hasattr(config, name), f"{name} yalnızca sunumda var"
        assert float(getattr(config, name)) == pytest.approx(float(value)), name


def test_disclaimer_matches():
    web = ts_constants(WEB_LIB / "config.ts")
    assert web["SKIN_DISCLAIMER"].strip('"') == config.SKIN_DISCLAIMER


def test_face_regions_match():
    web = ts_constants(WEB_LIB / "faceRegions.ts")
    as_list = lambda v: [int(x) for x in re.findall(r"\d+", v)]  # noqa: E731
    assert as_list(web["FOREHEAD"]) == regions.FOREHEAD
    assert as_list(web["RIGHT_CHEEK"]) == regions.RIGHT_CHEEK
    assert as_list(web["LEFT_CHEEK"]) == regions.LEFT_CHEEK
    assert as_list(web["RIGHT_EYE_EAR"]) == list(metrics.RIGHT_EYE_EAR)
    assert as_list(web["LEFT_EYE_EAR"]) == list(metrics.LEFT_EYE_EAR)
    for name in ("FOREHEAD_TOP", "CHIN", "CHEEK_RIGHT_EDGE", "CHEEK_LEFT_EDGE", "JAW_RIGHT", "JAW_LEFT"):
        assert int(web[name]) == getattr(metrics, name), name
