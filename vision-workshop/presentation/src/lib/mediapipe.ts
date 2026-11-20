// MediaPipe Tasks (tarayıcı) yükleyicisi. Model ve wasm dosyaları yerelden (public/) yüklenir;
// kamera görüntüsü hiçbir sunucuya gönderilmez. Modeller bir kez yüklenip önbellekte tutulur.
import { FaceLandmarker, FilesetResolver, HandLandmarker } from "@mediapipe/tasks-vision";

const asset = (p: string) => new URL(`${import.meta.env.BASE_URL}${p}`, window.location.href).href;

let fileset: ReturnType<typeof FilesetResolver.forVisionTasks> | null = null;
let face: Promise<FaceLandmarker> | null = null;
let hand: Promise<HandLandmarker> | null = null;

export class ModelLoadError extends Error {}

async function ensureFile(path: string) {
  const res = await fetch(asset(path), { method: "HEAD" });
  if (!res.ok) throw new ModelLoadError(`${path} bulunamadı (HTTP ${res.status}).`);
}

function getFileset() {
  fileset ??= FilesetResolver.forVisionTasks(asset("mediapipe/wasm"));
  return fileset;
}

export function getFaceLandmarker(): Promise<FaceLandmarker> {
  face ??= (async () => {
    await ensureFile("models/face_landmarker.task");
    return FaceLandmarker.createFromOptions(await getFileset(), {
      baseOptions: { modelAssetPath: asset("models/face_landmarker.task"), delegate: "CPU" },
      runningMode: "VIDEO",
      numFaces: 2,
      outputFaceBlendshapes: true,
      outputFacialTransformationMatrixes: true,
    });
  })().catch((e) => { face = null; throw e instanceof ModelLoadError ? e : new ModelLoadError(String(e)); });
  return face;
}

export function getHandLandmarker(): Promise<HandLandmarker> {
  hand ??= (async () => {
    await ensureFile("models/hand_landmarker.task");
    return HandLandmarker.createFromOptions(await getFileset(), {
      baseOptions: { modelAssetPath: asset("models/hand_landmarker.task"), delegate: "CPU" },
      runningMode: "VIDEO",
      numHands: 1,
    });
  })().catch((e) => { hand = null; throw e instanceof ModelLoadError ? e : new ModelLoadError(String(e)); });
  return hand;
}

/** VIDEO modu her çağrıda artan zaman damgası ister. */
let lastTs = 0;
export function nextTimestamp(): number {
  const t = performance.now();
  lastTs = t > lastTs ? t : lastTs + 1;
  return lastTs;
}

export const FACE_CONTOURS = FaceLandmarker.FACE_LANDMARKS_CONTOURS;
export const FACE_TESSELATION = FaceLandmarker.FACE_LANDMARKS_TESSELATION;
export const FACE_IRISES = [...FaceLandmarker.FACE_LANDMARKS_LEFT_IRIS, ...FaceLandmarker.FACE_LANDMARKS_RIGHT_IRIS];
