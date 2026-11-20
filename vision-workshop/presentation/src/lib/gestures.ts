// Python: src/hands/gestures.py ile aynı mantık (histerezis, bekleme, soğuma, el kaybında sıfırlama).
import * as C from "./config";
import { angleDeg, dist, type Pt } from "./geometry";

export const FINGERS: Record<string, [number, number, number, number]> = {
  "başparmak": [1, 2, 3, 4], "işaret": [5, 6, 7, 8], "orta": [9, 10, 11, 12],
  "yüzük": [13, 14, 15, 16], "serçe": [17, 18, 19, 20],
};

export const GESTURE_NAMES: Record<string, string> = {
  acik_el: "açık el", yumruk: "yumruk", isaret: "işaret parmağı", zafer: "V işareti",
  basparmak: "başparmak yukarı", belirsiz: "belirsiz",
};

export const palmSize = (p: Pt[]) => Math.max(dist(p[0], p[9]), 1e-6);
export const pinchRatio = (p: Pt[]) => dist(p[4], p[8]) / palmSize(p);

export type FingerState = boolean | null;

export function fingerStates(p: Pt[]): Record<string, FingerState> {
  const out: Record<string, FingerState> = {};
  for (const [name, [a, b, c, d]] of Object.entries(FINGERS)) {
    if (name === "başparmak") {
      const mcp = angleDeg(p[a], p[b], p[c]);
      const ip = angleDeg(p[b], p[c], p[d]);
      out[name] = mcp >= C.THUMB_EXTENDED_DEG && ip >= C.THUMB_EXTENDED_DEG ? true
        : mcp < C.THUMB_FOLDED_DEG || ip < C.THUMB_FOLDED_DEG ? false : null;
      continue;
    }
    const pip = angleDeg(p[a], p[b], p[c]);
    out[name] = pip >= C.FINGER_EXTENDED_DEG ? true : pip <= C.FINGER_FOLDED_DEG ? false : null;
  }
  return out;
}

export function classifyStatic(s: Record<string, FingerState>): string {
  const others = [s["işaret"], s["orta"], s["yüzük"], s["serçe"]];
  if (others.every((v) => v === true)) return "acik_el";
  if (others.every((v) => v === false)) return s["başparmak"] === true ? "basparmak" : "yumruk";
  if (s["işaret"] === true && others.slice(1).every((v) => v === false)) return "isaret";
  if (s["işaret"] === true && s["orta"] === true && s["yüzük"] === false && s["serçe"] === false) return "zafer";
  return "belirsiz";
}

export class Hysteresis {
  active = false;
  constructor(public enter: number, public exit: number) {}
  update(v: number) {
    if (!this.active && v < this.enter) this.active = true;
    else if (this.active && v > this.exit) this.active = false;
    return this.active;
  }
  reset() { this.active = false; }
}

export class Debouncer<T> {
  private candidate: T;
  private since: number | null = null;
  constructor(public stableMs: number, public value: T) { this.candidate = value; }
  update(c: T, t: number): T {
    if (c !== this.candidate) { this.candidate = c; this.since = t; }
    else if (c !== this.value && this.since !== null && t - this.since >= this.stableMs) this.value = c;
    return this.value;
  }
  reset(v: T) { this.value = this.candidate = v; this.since = null; }
}

export type GestureState = {
  present: boolean; gesture: string; raw: string; pinching: boolean; pinch: number; events: string[];
};

export class GestureController {
  private pinch = new Hysteresis(C.PINCH_ENTER_RATIO, C.PINCH_EXIT_RATIO);
  private pinchDb = new Debouncer<boolean>(C.GESTURE_STABLE_MS, false);
  private gestureDb = new Debouncer<string>(C.GESTURE_STABLE_MS, "belirsiz");
  private lastCommand = -1e9;
  private lastSeen: number | null = null;
  private lostReported = true;
  state: GestureState = { present: false, gesture: "belirsiz", raw: "belirsiz", pinching: false, pinch: 1, events: [] };

  reset() {
    this.pinch.reset(); this.pinchDb.reset(false); this.gestureDb.reset("belirsiz");
    this.state = { present: false, gesture: "belirsiz", raw: "belirsiz", pinching: false, pinch: 1, events: [] };
  }

  update(points: Pt[] | null, t: number): GestureState {
    const events: string[] = [];
    if (!points) {
      if (this.lastSeen !== null && !this.lostReported && t - this.lastSeen >= C.HAND_LOST_RESET_MS) {
        if (this.state.pinching) events.push("pinch_bitti");
        this.reset();
        this.lostReported = true;
        events.push("el_kayboldu");
      }
      this.state = { ...this.state, present: false, events };
      return this.state;
    }
    this.lastSeen = t;
    this.lostReported = false;
    const value = pinchRatio(points);
    const stable = this.pinchDb.update(this.pinch.update(value), t);
    if (stable && !this.state.pinching) events.push("pinch_basladi");
    else if (!stable && this.state.pinching) events.push("pinch_bitti");
    const raw = classifyStatic(fingerStates(points));
    const previous = this.state.gesture;
    const gesture = this.gestureDb.update(raw, t);
    if (gesture !== previous && gesture !== "belirsiz" && t - this.lastCommand >= C.COMMAND_COOLDOWN_MS) {
      events.push(`jest:${gesture}`);
      this.lastCommand = t;
    }
    this.state = { present: true, gesture, raw, pinching: stable, pinch: value, events };
    return this.state;
  }
}
