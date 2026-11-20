import type { ComponentType } from "react";
import type { SceneProps } from "./types";
import { Acilis, Rota } from "./intro";
import { Esik, Renk, Roi, Roller, Veri } from "./basics";
import { DemoYuz, Geometri, Iz, Normalize, Takip } from "./face";
import { DemoEl, El, Kararlilik } from "./hands";
import { Bolgeler, DemoCilt, Isik, Model } from "./skin";
import { Final, Gorevler, Karsilastirma, Mimari, Sonraki } from "./project";

// Sahne kimliği -> bileşen. Sıra ve metinler meta.js içindedir.
export const COMPONENTS: Record<string, ComponentType<SceneProps>> = {
  acilis: Acilis, rota: Rota,
  veri: Veri, renk: Renk, roi: Roi, esik: Esik, roller: Roller,
  takip: Takip, "demo-yuz": DemoYuz, normalize: Normalize, iz: Iz, geometri: Geometri,
  el: El, kararlilik: Kararlilik, "demo-el": DemoEl,
  bolgeler: Bolgeler, isik: Isik, "demo-cilt": DemoCilt, model: Model,
  "kaynaklar-karsilastirma": Karsilastirma, mimari: Mimari, gorevler: Gorevler, final: Final, sonraki: Sonraki,
};
