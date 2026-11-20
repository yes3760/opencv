// Python tarafındaki src/config.py ile aynı adlar ve değerler.
// tests/test_config_sync.py iki dosyanın ortak değerlerinin eşit olduğunu denetler.
export const PINCH_ENTER_RATIO = 0.25;
export const PINCH_EXIT_RATIO = 0.40;
export const FINGER_EXTENDED_DEG = 150.0;
export const FINGER_FOLDED_DEG = 120.0;
export const THUMB_EXTENDED_DEG = 145.0;
export const THUMB_FOLDED_DEG = 135.0;
export const GESTURE_STABLE_MS = 120;
export const COMMAND_COOLDOWN_MS = 700;
export const HAND_LOST_RESET_MS = 300;
export const EMA_ALPHA = 0.35;
export const TRAIL_LENGTH = 45;
export const FRONTAL_MAX_YAW_DEG = 15.0;
export const FRONTAL_MAX_PITCH_DEG = 20.0;
export const FRONTAL_MAX_ROLL_DEG = 12.0;
export const SKIN_MIN_FACE_WIDTH_PX = 180;
export const SKIN_MAX_YAW_DEG = 12.0;
export const SKIN_MAX_PITCH_DEG = 20.0;
export const SKIN_MAX_ROLL_DEG = 10.0;
export const SKIN_MIN_SHARPNESS = 20.0;
export const SKIN_MIN_MEDIAN_L = 50;
export const SKIN_MAX_MEDIAN_L = 235;
export const SKIN_MAX_CLIPPED_FRACTION = 0.08;
export const SKIN_MAX_DARK_FRACTION = 0.10;
export const SKIN_ROI_EROSION_RATIO = 0.015;
export const SKIN_MIN_VALID_FRACTION = 0.5;
export const SPECULAR_DELTA_L = 25;
export const SPECULAR_CHROMA_RATIO = 0.7;
export const SKIN_ANALYSIS_FACE_WIDTH = 320;
export const SKIN_DISCLAIMER = "Eğitim amaçlı görüntü analizi; tıbbi tanı değildir.";

/** Isı haritası için sabit gösterim aralığı (Δa*), Python: skin/metrics.py MAP_RANGES */
export const REDNESS_RANGE: [number, number] = [-10, 10];
