from __future__ import annotations
import numpy as np
from core.image_io import to_gray
from generators.height import _blur

def generate_normal(height: np.ndarray, strength: float = 4.0, blur: float = 0.0,
                    convention: str = "opengl") -> np.ndarray:
    h = np.asarray(height)
    if h.ndim == 3:
        h = to_gray(h)
    else:
        scale = 65535.0 if h.dtype == np.uint16 else 255.0
        h = h.astype(np.float32) / scale
    h = h.astype(np.float32)
    if blur > 0:
        h = _blur(h, blur)
    dy, dx = np.gradient(h)
    nx = -dx * float(strength) * max(1, h.shape[1])
    ny = -dy * float(strength) * max(1, h.shape[0])
    if convention.lower() in ("directx", "dx", "y-"):
        ny = -ny
    elif convention.lower() not in ("opengl", "gl", "y+"):
        raise ValueError("Convention must be OpenGL or DirectX")
    nz = np.ones_like(h)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack((nx / length, ny / length, nz / length), axis=-1)
    return np.round(np.clip(normal * 0.5 + 0.5, 0.0, 1.0) * 255).astype(np.uint8)
