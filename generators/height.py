from __future__ import annotations
import numpy as np
from core.image_io import to_gray
try:
    import cv2
except ImportError:
    cv2 = None

def _blur(image: np.ndarray, radius: float) -> np.ndarray:
    if radius <= 0:
        return image
    if cv2 is not None:
        k = max(3, int(round(radius * 4)) | 1)
        return cv2.GaussianBlur(image.astype(np.float32), (k, k), radius)
    r = max(1, int(round(radius)))
    padded = np.pad(image, ((0, 0), (r, r)), mode="reflect")
    horizontal = sum(padded[:, i:i + image.shape[1]] for i in range(2 * r + 1)) / (2 * r + 1)
    padded = np.pad(horizontal, ((r, r), (0, 0)), mode="reflect")
    return sum(padded[i:i + image.shape[0], :] for i in range(2 * r + 1)) / (2 * r + 1)

def generate_height(source: np.ndarray, method: str = "luminance", contrast: float = 1.0,
                    brightness: float = 0.0, detail: float = 0.0, blur: float = 0.0,
                    invert: bool = False) -> np.ndarray:
    gray = to_gray(source)
    if method == "edges":
        gy, gx = np.gradient(gray)
        result = np.sqrt(gx * gx + gy * gy)
        lo, hi = float(result.min()), float(result.max())
        result = (result - lo) / (hi - lo) if hi > lo else np.zeros_like(result)
    elif method == "combined":
        gy, gx = np.gradient(gray)
        edge = np.sqrt(gx * gx + gy * gy)
        edge /= max(float(edge.max()), 1e-8)
        result = np.clip(gray * 0.8 + edge * 0.2, 0.0, 1.0)
    elif method in ("grayscale", "luminance"):
        result = gray.copy()
    else:
        raise ValueError(f"Unknown height method: {method}")
    if blur > 0:
        result = _blur(result, blur)
    if detail:
        base = _blur(result, max(1.0, blur + 1.0))
        result = result + (result - base) * float(detail)
    result = (result - 0.5) * float(contrast) + 0.5 + float(brightness)
    result = np.clip(result, 0.0, 1.0)
    if invert:
        result = 1.0 - result
    return np.round(result * 255).astype(np.uint8)
