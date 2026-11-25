from __future__ import annotations
import numpy as np
from core.image_io import to_gray
from generators.height import _blur

def generate_roughness(source: np.ndarray, method: str = "detail", contrast: float = 1.0,
                       brightness: float = 0.0, gamma: float = 1.0,
                       detail: float = 0.5, blur: float = 0.0,
                       invert: bool = False) -> np.ndarray:
    gray = to_gray(source)
    if method == "brightness":
        result = gray
    elif method == "detail":
        local = _blur(gray, 2.0)
        variation = np.abs(gray - local)
        variation /= max(float(variation.max()), 1e-8)
        result = np.clip(0.65 * gray + 0.35 * variation * float(detail), 0.0, 1.0)
    elif method == "local_contrast":
        local = _blur(gray, 3.0)
        variation = np.abs(gray - local)
        result = np.clip(0.5 + (variation - 0.08) * 2.5 * float(detail), 0.0, 1.0)
    else:
        raise ValueError(f"Unknown roughness method: {method}")
    if blur > 0:
        result = _blur(result, blur)
    result = (result - 0.5) * float(contrast) + 0.5 + float(brightness)
    result = np.clip(result, 0.0, 1.0)
    result = np.power(result, 1.0 / max(0.01, float(gamma)))
    if invert:
        result = 1.0 - result
    return np.round(result * 255).astype(np.uint8)
