"""Öğrenci raporunu (Markdown) organizasyon bilgileriyle doldurup HTML ve PDF üretir.

Çalıştırma: python docs/tools/build_report.py
Gerekenler: pandoc (3.x) ve Google Chrome veya Chromium (PDF için).

Organizasyon bilgileri yalnızca workshop.config.json dosyasından okunur. Boş alanlar
köşeli parantezli yer tutucu olarak kalır.
"""

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
BUILD = DOCS / "build"

PLACEHOLDERS = {
    "universite": "Üniversite adı", "topluluk": "Topluluk adı", "egitmen": "Eğitmen adı",
    "sponsor": "Destekleyen kurum (varsa)", "tarih": "Tarih", "yer": "Yer", "iletisim": "İletişim",
    "depo_baglantisi": "Depo bağlantısı",
}

CHROME_CANDIDATES = {
    "Darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
               "/Applications/Chromium.app/Contents/MacOS/Chromium"],
    "Windows": [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "Linux": ["google-chrome", "chromium", "chromium-browser"],
}


def fill(text: str, config: dict) -> str:
    def repl(match):
        key = match.group(1)
        value = str(config.get(key, "")).strip()
        if value:
            return value
        return f'<span class="placeholder">[{PLACEHOLDERS.get(key, key)}]</span>'
    return re.sub(r"\{\{(\w+)\}\}", repl, text)


def find_chrome(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    for candidate in CHROME_CANDIDATES.get(platform.system(), []):
        path = shutil.which(candidate) or (candidate if Path(candidate).exists() else None)
        if path:
            return path
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Öğrenci raporunu üret")
    parser.add_argument("--chrome", help="Chrome/Chromium çalıştırılabilir dosyasının yolu")
    parser.add_argument("--source", default=str(DOCS / "OGRENCI_RAPORU.md"))
    parser.add_argument("--output", default=str(DOCS / "OGRENCI_RAPORU.pdf"))
    args = parser.parse_args()

    if not shutil.which("pandoc"):
        print("pandoc bulunamadı: https://pandoc.org/installing.html")
        return 1
    config = json.loads((ROOT / "workshop.config.json").read_text(encoding="utf-8"))
    BUILD.mkdir(exist_ok=True)
    source = Path(args.source)
    filled = BUILD / (source.stem + ".filled.md")
    filled.write_text(fill(source.read_text(encoding="utf-8"), config), encoding="utf-8")
    html = BUILD / (source.stem + ".html")
    cmd = ["pandoc", str(filled), "-o", str(html), "--standalone", "--embed-resources", "--toc",
           "--toc-depth=2", f"--css={DOCS / 'tools' / 'report.css'}", f"--resource-path={DOCS}",
           "--metadata", "lang=tr", "--syntax-highlighting=pygments"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and "syntax-highlighting" in result.stderr:
        cmd[-1] = "--highlight-style=pygments"          # eski pandoc sürümleri
        result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        return 1
    # İçindekiler tablosu künye ve uyarı kutusundan sonraya, kapak sayfasına taşınır.
    page = html.read_text(encoding="utf-8")
    toc = re.search(r'<nav id="TOC".*?</nav>', page, flags=re.S)
    anchor = page.find('<div class="uyari">')
    if toc and anchor != -1:
        page = page.replace(toc.group(0), "", 1)
        close = page.find("</div>", page.find('<div class="uyari">')) + len("</div>")
        page = page[:close] + "\n" + toc.group(0) + page[close:]
        html.write_text(page, encoding="utf-8")
    print(f"HTML: {html}")

    chrome = find_chrome(args.chrome)
    if not chrome:
        print("Chrome bulunamadı; HTML dosyası tarayıcıda açılıp 'PDF olarak kaydet' ile yazdırılabilir.")
        return 0
    out = Path(args.output).resolve()
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--run-all-compositor-stages-before-draw", f"--print-to-pdf={out}", html.resolve().as_uri()],
                   check=True, capture_output=True)
    print(f"PDF : {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
