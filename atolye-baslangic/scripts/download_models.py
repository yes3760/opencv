"""Model dosyalarını resmî kaynaktan indirir ve SHA-256 özetiyle doğrular.

Çalıştırma : python scripts/download_models.py
Yalnızca Python standart kütüphanesini kullanır (certifi varsa sertifikaları için onu kullanır).
İndirme bir kez yapılır; sonrasında uygulama internet olmadan çalışır.

Kaynak: MediaPipe resmî model deposu (storage.googleapis.com/mediapipe-models).
Sürüm numaralı adresler (".../1/...") kullanılır; "latest" adresi zamanla değişebilir.
Özetler 2026-10-19 tarihinde indirilen dosyalardan hesaplanmıştır.
"""

import hashlib
import ssl
import sys
import urllib.request
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
BASE = "https://storage.googleapis.com/mediapipe-models"

MODELS = [
    {
        "file": "face_landmarker.task",
        "url": f"{BASE}/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        "sha256": "64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff",
        "size": 3758596,
        "required": True,
    },
    {
        "file": "hand_landmarker.task",
        "url": f"{BASE}/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        "sha256": "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1",
        "size": 7819105,
        "required": True,
    },
    {
        "file": "selfie_multiclass_256x256.tflite",
        "url": f"{BASE}/image_segmenter/selfie_multiclass_256x256/float32/1/selfie_multiclass_256x256.tflite",
        "sha256": "c6748b1253a99067ef71f7e26ca71096cd449baefa8f101900ea23016507e0e0",
        "size": 16371837,
        "required": False,   # cilt modülü bu model olmadan da çalışır
    },
]


def ssl_context():
    """python.org'dan kurulan macOS Python'unda sertifika deposu boş olabilir.
    certifi (MediaPipe ile birlikte kurulur) varsa onun sertifikaları kullanılır."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(model: dict) -> bool:
    target = MODEL_DIR / model["file"]
    if target.exists() and sha256(target) == model["sha256"]:
        print(f"[tamam]  {model['file']} zaten var ve doğrulandı.")
        return True
    print(f"[indir]  {model['file']} ({model['size'] / 1e6:.1f} MB) ...")
    temp = target.with_suffix(target.suffix + ".part")
    try:
        with urllib.request.urlopen(model["url"], timeout=60, context=ssl_context()) as response, \
                temp.open("wb") as out:
            while chunk := response.read(1 << 16):
                out.write(chunk)
    except OSError as exc:
        temp.unlink(missing_ok=True)
        print(f"[hata]   {model['file']} indirilemedi: {exc}")
        return False
    if sha256(temp) != model["sha256"]:
        temp.unlink(missing_ok=True)
        print(f"[hata]   {model['file']} özeti beklenenden farklı; dosya silindi.")
        return False
    temp.replace(target)
    print(f"[tamam]  {model['file']} indirildi ve doğrulandı.")
    return True


def main() -> int:
    MODEL_DIR.mkdir(exist_ok=True)
    results = [(m, download(m)) for m in MODELS]
    missing_required = [m["file"] for m, ok in results if not ok and m["required"]]
    if missing_required:
        print("Zorunlu modeller eksik: " + ", ".join(missing_required))
        return 1
    print("Modeller hazır. Sıradaki adım: python scripts/check_setup.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
