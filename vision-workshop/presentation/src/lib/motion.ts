import { useEffect, useRef, useState } from "react";

/** prefers-reduced-motion tercihini izler. */
export function useReducedMotion(): boolean {
  const query = "(prefers-reduced-motion: reduce)";
  const [reduced, setReduced] = useState(() => window.matchMedia?.(query).matches ?? false);
  useEffect(() => {
    const mq = window.matchMedia?.(query);
    if (!mq) return;
    const on = () => setReduced(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return reduced;
}

/** requestAnimationFrame döngüsü; running false iken durur. */
export function useAnimationFrame(cb: (t: number, dt: number) => void, running = true) {
  const ref = useRef(cb);
  ref.current = cb;
  useEffect(() => {
    if (!running) return;
    let id = 0, last = performance.now();
    const loop = (t: number) => { ref.current(t, Math.min(100, t - last)); last = t; id = requestAnimationFrame(loop); };
    id = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(id);
  }, [running]);
}
