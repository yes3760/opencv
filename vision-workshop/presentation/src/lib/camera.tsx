// Kamera yönetimi: kamera yalnızca "Kamerayı başlat" düğmesiyle açılır, "Durdur" ile
// bütün izler (track) kapatılır. Sahne değişince App kamerayı durdurur.
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

export type CamErrorKind = "denied" | "notfound" | "busy" | "insecure" | "unsupported" | "unknown";
export type CamError = { kind: CamErrorKind; title: string; hint: string };
export type SourceState =
  | { status: "idle" }
  | { status: "starting" }
  | { status: "camera"; stream: MediaStream }
  | { status: "file"; url: string; name: string }
  | { status: "error"; error: CamError };

const ERRORS: Record<CamErrorKind, Omit<CamError, "kind">> = {
  denied: { title: "Kamera izni reddedildi", hint: "Adres çubuğundaki kamera simgesinden izin verip tekrar deneyin. İsterseniz örnek gösterimle devam edebilirsiniz." },
  notfound: { title: "Kamera bulunamadı", hint: "Bilgisayarda kullanılabilir bir kamera görünmüyor. Video dosyası seçebilir veya örnek gösterimi kullanabilirsiniz." },
  busy: { title: "Kamera kullanımda", hint: "Kamera başka bir uygulamada açık olabilir (Zoom, Teams, Python uygulaması). Kapatıp tekrar deneyin." },
  insecure: { title: "Güvenli bağlantı gerekli", hint: "Tarayıcılar kamerayı yalnızca https:// veya http://localhost adreslerinde açar. Sunumu 'npm run dev' ile localhost üzerinden açın." },
  unsupported: { title: "Tarayıcı kamera erişimini desteklemiyor", hint: "Güncel bir Chrome, Edge, Firefox veya Safari kullanın." },
  unknown: { title: "Kamera açılamadı", hint: "Sayfayı yenileyip tekrar deneyin." },
};

export function mapCameraError(e: unknown): CamError {
  const name = (e as { name?: string })?.name ?? "";
  const kind: CamErrorKind =
    name === "NotAllowedError" || name === "PermissionDeniedError" ? "denied"
      : name === "NotFoundError" || name === "OverconstrainedError" || name === "DevicesNotFoundError" ? "notfound"
        : name === "NotReadableError" || name === "TrackStartError" || name === "AbortError" ? "busy"
          : name === "SecurityError" ? "insecure" : "unknown";
  return { kind, ...ERRORS[kind] };
}

export type CameraDevice = { id: string; label: string };

type Ctx = {
  source: SourceState;
  devices: CameraDevice[];            // izin verildikten sonra listelenen kameralar
  deviceId: string | null;            // açık kameranın kimliği
  start: (deviceId?: string) => Promise<void>;
  stop: () => void;
  openFile: (file: File) => void;
};

const CameraContext = createContext<Ctx | null>(null);

export function CameraProvider({ children }: { children: ReactNode }) {
  const [source, setSource] = useState<SourceState>({ status: "idle" });
  const [devices, setDevices] = useState<CameraDevice[]>([]);
  const [deviceId, setDeviceId] = useState<string | null>(null);
  const current = useRef<SourceState>(source);
  current.current = source;

  const release = useCallback(() => {
    const s = current.current;
    if (s.status === "camera") s.stream.getTracks().forEach((t) => t.stop());
    if (s.status === "file") URL.revokeObjectURL(s.url);
  }, []);

  const stop = useCallback(() => {
    release();
    setSource({ status: "idle" });
  }, [release]);

  const start = useCallback(async (wanted?: string) => {
    release();
    if (!window.isSecureContext) { setSource({ status: "error", error: { kind: "insecure", ...ERRORS.insecure } }); return; }
    if (!navigator.mediaDevices?.getUserMedia) { setSource({ status: "error", error: { kind: "unsupported", ...ERRORS.unsupported } }); return; }
    setSource({ status: "starting" });
    try {
      // Bilgisayarda birden fazla kamera olabilir (ör. Mac'te iPhone Süreklilik Kamerası);
      // seçilen kamera varsa o açılır, yoksa tarayıcının varsayılanı.
      const video: MediaTrackConstraints = { width: { ideal: 1280 }, height: { ideal: 720 } };
      if (wanted) video.deviceId = { exact: wanted }; else video.facingMode = "user";
      const stream = await navigator.mediaDevices.getUserMedia({ video, audio: false });
      setDeviceId(stream.getVideoTracks()[0]?.getSettings().deviceId ?? null);
      // Kamera adları ancak izin verildikten sonra görünür.
      const all = await navigator.mediaDevices.enumerateDevices().catch(() => []);
      setDevices(all.filter((d) => d.kind === "videoinput")
        .map((d, i) => ({ id: d.deviceId, label: d.label || `Kamera ${i + 1}` })));
      setSource({ status: "camera", stream });
    } catch (e) {
      setSource({ status: "error", error: mapCameraError(e) });
    }
  }, [release]);

  const openFile = useCallback((file: File) => {
    release();
    setSource({ status: "file", url: URL.createObjectURL(file), name: file.name });
  }, [release]);

  useEffect(() => () => release(), [release]);   // sayfa kapanınca kamerayı bırak

  const value = useMemo(() => ({ source, devices, deviceId, start, stop, openFile }),
    [source, devices, deviceId, start, stop, openFile]);
  return <CameraContext.Provider value={value}>{children}</CameraContext.Provider>;
}

export function useCamera(): Ctx {
  const ctx = useContext(CameraContext);
  if (!ctx) throw new Error("CameraProvider eksik");
  return ctx;
}
