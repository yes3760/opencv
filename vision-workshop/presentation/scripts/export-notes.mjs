// docs/EGITMEN_NOTLARI.md dosyasını sahne verisinden (src/scenes/meta.js) üretir.
// Sunumdaki notlar ile belge her zaman aynı kalsın diye notlar elle değil bu betikle yazılır.
// Çalıştırma: npm run notes
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { SCENES, SECTIONS, SESSION_FLOW } from "../src/scenes/meta.js";

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, "..", "..", "docs", "EGITMEN_NOTLARI.md");
const num = (id) => String(SCENES.findIndex((s) => s.id === id) + 1).padStart(2, "0");
const L = [];

L.push("# VISION LAB — Eğitmen notları ve oturum akışı", "");
L.push("Bu belge `presentation/src/scenes/meta.js` dosyasından `npm run notes` komutuyla üretilir;",
  "sunumdaki \"Notlar\" paneli ve sunucu penceresi aynı metinleri gösterir.", "");

L.push("## Sunumun kullanımı", "");
L.push("| İşlem | Kısayol veya yol |", "|---|---|");
L.push("| Sonraki / önceki sahne | Sağ ve sol ok, alttaki ← → düğmeleri, dokunmatik ekranda yatay kaydırma |");
L.push("| İlk sahne | Home |", "| Uygulama içi tam ekran | F (Esc ile çıkılır) |");
L.push("| Açık katmanları kapatma | Esc (bölüm menüsü, notlar, kod) |");
L.push("| Notlar paneli | N veya üstteki \"Notlar\" |", "| Bölüm menüsü | M veya üstteki \"Bölümler\" |");
L.push("| Sunucu penceresi | Üstteki \"Sunucu penceresi\": notlar, sıradaki sahne ve geçen süre ayrı pencerede; ana sunumu izler |");
L.push("| Kodu göster | Alttaki \"Kodu göster\": Python dosyası, çalıştırma komutu ve kod parçası |", "");
L.push("Kısayollar metin alanlarında ve sürgülerde devre dışıdır. Adres çubuğundaki `#/9` gibi sahne",
  "numarası doğrudan o sahneyi açar.", "");

L.push("## Oturum öncesi hazırlık (eğitmen)", "");
L.push("1. Proje kökünde `python scripts/download_models.py` ve `python scripts/check_setup.py --kamera` çalıştırılır.");
L.push("2. `presentation` klasöründe `npm install` (bir kez) ve `npm run dev`; sunum `http://localhost:5173` adresinde açılır.");
L.push("   Kamera yalnızca `localhost` veya HTTPS adresinde açılır; ağ üzerinden IP adresiyle açılan sunumda kamera çalışmaz.");
L.push("3. Canlı demo sahnelerinden biri (09) açılıp \"Kamerayı başlat\" ile kamera izni önceden verilir.");
L.push("4. Projeksiyon bağlıysa \"Sunucu penceresi\" dizüstü ekranına, sunum projeksiyona alınır ve F ile tam ekran yapılır.");
L.push("5. Yedek plan: kamera veya model sorununda her canlı demoda \"Örnek gösterim\" ve \"Video dosyası seç\" seçenekleri vardır.");
L.push("6. Mac'te birden fazla kamera varsa (ör. iPhone Süreklilik Kamerası) Python uygulaması `--source auto` ile görüntü veren kamerayı seçer.", "");

L.push("## Gizlilik ve katılım", "");
L.push("- Kamera kullanımı gönüllüdür; kamerasız katılım için video/fotoğraf dosyası veya örnek gösterim kullanılır.");
L.push("- Python uygulaması ve sunum görüntü kaydetmez ve hiçbir sunucuya göndermez. `--snapshot` yalnızca açıkça verildiğinde son ekranı kaydeder.");
L.push("- Cilt bölümünde uyarı metni her zaman görünür: \"Eğitim amaçlı görüntü analizi; tıbbi tanı değildir.\"");
L.push("- Katılımcıların yüzleri üzerinden kişilik, duygu veya sağlık yorumu yapılmaz; ekranda gösterilen değerler görünüm ölçümüdür.", "");

L.push("## Oturum akışı", "");
L.push("Her oturum 75 dk eğitim ve uygulama + 15 dk ara + 90 dk eğitim ve uygulama = 180 dk. Toplam 12 saat; 11 saati eğitim ve uygulama.", "");
for (const s of SESSION_FLOW) {
  const total = s.slots.reduce((a, x) => a + x[2], 0);
  L.push(`### Oturum ${s.session}: ${s.title} (${total} dk)`, "", `Öğrenme çıktısı: ${s.outcome}`, "");
  L.push("| Başlangıç | Konu | Süre | Sahne | Python dosyası |", "|---|---|---|---|---|");
  for (const [t, topic, min, ids, file] of s.slots) {
    L.push(`| ${t} | ${topic} | ${min} dk | ${ids.map(num).join(", ") || "—"} | ${file ? "`" + file + "`" : "—"} |`);
  }
  L.push("");
}

L.push("## Tek günlük 6 saatlik kısa sürüm", "");
L.push("Toplam 360 dk: 300 dk eğitim ve uygulama, 60 dk ara (15 + 30 + 15). Kurulum önceden tamamlanmış olmalıdır.", "");
L.push("| Blok | Süre | Sahneler | Uygulamalı | Yalnızca gösterim |", "|---|---|---|---|---|");
L.push(`| 1 | 75 dk | ${["acilis", "rota", "veri", "renk", "roi", "esik"].map(num).join(", ")} | 01, 02 | 03 (filtre, eşik, morfoloji, kontur) |`);
L.push("| Ara | 15 dk | | | |");
L.push(`| 2 | 80 dk | ${["roller", "takip", "demo-yuz", "normalize", "geometri"].map(num).join(", ")} | 04, 05, 06 (EAR ve poz) | Haar karşılaştırması, One Euro, yüz şekli eğilimi (${num("iz")}) |`);
L.push("| Öğle arası | 30 dk | | | |");
L.push(`| 3 | 75 dk | ${["el", "kararlilik", "demo-el"].map(num).join(", ")} | 07, 08 (sürgü) | Çizim ve sürükleme, soğuma süresi ayarı |`);
L.push("| Ara | 15 dk | | | |");
L.push(`| 4 | 70 dk | ${["bolgeler", "isik", "demo-cilt", "model", "final", "sonraki"].map(num).join(", ")} | 09, 10 | Segmentasyon modeli, ısı haritası yorumu, açık kaynak model tartışması (${num("kaynaklar-karsilastirma")}) |`);
L.push("", "Kısa sürümde hiçbir cilt modeli eğitilmez; Seviye 2 yalnızca hazır segmentasyon modelinin gösterimi ve akne derecelendirme modelinin neden entegre edilmediğinin tartışmasıdır.", "");

L.push("## Sahne notları", "");
for (const sec of SECTIONS) {
  L.push(`### ${sec}`, "");
  SCENES.forEach((s, i) => {
    if (s.section !== sec) return;
    L.push(`#### ${String(i + 1).padStart(2, "0")} · ${s.title}`, "");
    L.push(`Oturum ${s.session} · yaklaşık ${s.minutes} dk${s.camera ? " · canlı demo (kamera isteğe bağlı)" : ""}`, "");
    for (const n of s.notes) L.push(`- ${n}`);
    if (s.code) L.push("", `Kod: \`${s.code.file}\` · Çalıştırma: \`${s.code.run}\``);
    L.push("");
  });
}
writeFileSync(out, L.join("\n"));
console.log(`[tamam] ${out}`);
