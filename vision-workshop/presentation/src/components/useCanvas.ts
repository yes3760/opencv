import { useEffect, useRef } from "react";

/** Sabit mantıksal boyutta, keskin çizim için 2x çözünürlüklü tuval. */
export function useCanvas(width: number, height: number, draw: (g: CanvasRenderingContext2D) => void, deps: unknown[]) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const k = 2;
    if (c.width !== width * k) { c.width = width * k; c.height = height * k; }
    const g = c.getContext("2d")!;
    g.setTransform(k, 0, 0, k, 0, 0);
    g.clearRect(0, 0, width, height);
    draw(g);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return ref;
}

export function prepCanvas(c: HTMLCanvasElement, width: number, height: number) {
  const k = 2;
  if (c.width !== width * k) { c.width = width * k; c.height = height * k; }
  const g = c.getContext("2d")!;
  g.setTransform(k, 0, 0, k, 0, 0);
  g.clearRect(0, 0, width, height);
  return g;
}
