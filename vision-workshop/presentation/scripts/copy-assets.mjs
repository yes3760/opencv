// MediaPipe WebAssembly dosyalarını ve model dosyalarını public/ klasörüne kopyalar.
// Böylece sunum, kurulumdan sonra internet olmadan ve sabit sürümlerle çalışır.
// Modeller Python projesiyle ortaktır: ../models (python scripts/download_models.py ile indirilir).
import { copyFileSync, existsSync, mkdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const wasmSrc = join(root, "node_modules", "@mediapipe", "tasks-vision", "wasm");
const wasmDst = join(root, "public", "mediapipe", "wasm");
const modelSrc = join(root, "..", "models");
const modelDst = join(root, "public", "models");

mkdirSync(wasmDst, { recursive: true });
mkdirSync(modelDst, { recursive: true });

for (const f of ["vision_wasm_internal.js", "vision_wasm_internal.wasm",
                 "vision_wasm_nosimd_internal.js", "vision_wasm_nosimd_internal.wasm"]) {
  const src = join(wasmSrc, f);
  if (!existsSync(src)) {
    console.error(`[hata] ${f} bulunamadı. Önce 'npm install' çalıştırın.`);
    process.exit(1);
  }
  copyFileSync(src, join(wasmDst, f));
}
console.log("[tamam] MediaPipe wasm dosyaları kopyalandı.");

let missing = 0;
for (const f of ["face_landmarker.task", "hand_landmarker.task"]) {
  const src = join(modelSrc, f);
  if (existsSync(src) && statSync(src).size > 0) {
    copyFileSync(src, join(modelDst, f));
    console.log(`[tamam] ${f} kopyalandı.`);
  } else {
    missing++;
    console.warn(`[uyarı] ${f} yok. Proje kökünde 'python scripts/download_models.py' çalıştırın. ` +
                 "Sunum yine açılır; canlı demolar 'Model yüklenemedi' ekranı gösterir, örnek gösterim çalışır.");
  }
}
if (missing === 0) console.log("Sunum hazır: npm run dev");
