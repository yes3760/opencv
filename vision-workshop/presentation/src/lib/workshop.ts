// Organizasyon bilgileri tek yerden gelir: proje kökündeki workshop.config.json
import raw from "../../../workshop.config.json";

type Config = Record<string, string>;
const cfg = raw as unknown as Config;

const LABELS: Record<string, string> = {
  universite: "Üniversite adı", topluluk: "Topluluk adı", egitmen: "Eğitmen adı",
  sponsor: "Destekleyen kurum", tarih: "Tarih", yer: "Yer", iletisim: "İletişim",
  depo_baglantisi: "Depo bağlantısı",
};

/** Değer boşsa köşeli parantezli yer tutucu döner; arayüz bunu soluk gösterir. */
export function field(key: string): { text: string; placeholder: boolean } {
  const value = (cfg[key] ?? "").trim();
  if (value) return { text: value, placeholder: false };
  return { text: `[${LABELS[key] ?? key}]`, placeholder: true };
}

export const TITLE = cfg.egitim_adi || "VISION LAB — Kameradan Etkileşime";
export const SUBTITLE = cfg.alt_baslik || "OpenCV ile Yüz, El ve Cilt Görünümü Analizi";
