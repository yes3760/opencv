// Python: src/skin/regions.py ile aynı MediaPipe Face Mesh nokta numaraları.
// Bölge adları kişinin kendi sağına/soluna göredir.
export const FOREHEAD = [67, 109, 10, 338, 297, 299, 296, 336, 9, 107, 66, 69];
export const RIGHT_CHEEK = [116, 117, 118, 119, 100, 36, 205, 187, 147, 123];
export const LEFT_CHEEK = [345, 346, 347, 348, 329, 266, 425, 411, 376, 352];

export const REGIONS: Record<string, number[]> = {
  "alın": FOREHEAD,
  "sağ yanak": RIGHT_CHEEK,
  "sol yanak": LEFT_CHEEK,
};

// Python: src/face/metrics.py
export const RIGHT_EYE_EAR = [33, 160, 158, 133, 153, 144];
export const LEFT_EYE_EAR = [362, 385, 387, 263, 373, 380];
export const MOUTH_INNER = [13, 14];
export const MOUTH_CORNERS = [78, 308];
export const FOREHEAD_TOP = 10;
export const CHIN = 152;
export const CHEEK_RIGHT_EDGE = 234;
export const CHEEK_LEFT_EDGE = 454;
export const JAW_RIGHT = 172;
export const JAW_LEFT = 397;
