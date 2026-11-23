"""Model dosyalarının varlık kontrolü ve MediaPipe seçeneklerinin hazırlanması."""

from __future__ import annotations

from pathlib import Path

import mediapipe as mp

BaseOptions = mp.tasks.BaseOptions
vision = mp.tasks.vision


class ModelMissingError(FileNotFoundError):
    """Model dosyası bulunamadığında fırlatılır; çözüm yolunu mesajında taşır."""


def require_model(path: Path) -> Path:
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise ModelMissingError(
            f"Model dosyası bulunamadı: {path.name}. Proje klasöründe şu komutu çalıştırın: "
            "python scripts/download_models.py"
        )
    return path


def base_options(path: Path) -> BaseOptions:
    """Modeli CPU üzerinde çalıştıracak temel seçenekler."""
    return BaseOptions(model_asset_path=str(require_model(path)))
