from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from core.image_io import save_image

def export_maps(directory: str | Path, material_name: str, source: np.ndarray,
                maps: dict[str, np.ndarray], extension: str = "png",
                normal_convention: str = "opengl", overwrite: bool = False) -> list[Path]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    ext = extension.lower().lstrip(".")
    if ext not in ("png", "tga", "tif", "tiff"):
        raise ValueError("Export format must be PNG, TGA or TIFF")
    payload = {"albedo": source, **maps}
    outputs = [directory / f"{material_name}_{key.title()}.{ext}" for key in payload]
    metadata_path = directory / "MaterialInfo.json"
    conflicts = [p for p in [*outputs, metadata_path] if p.exists()]
    if conflicts and not overwrite:
        raise FileExistsError("Existing files: " + ", ".join(p.name for p in conflicts))
    for (key, array), output in zip(payload.items(), outputs):
        save_image(output, array)
    info = {"name": material_name, "format": "PBRForge Material Package",
            "normal_convention": normal_convention,
            "textures": {key: output.name for key, output in zip(payload, outputs)},
            "notes": {"roughness": "Procedural estimate; artist review recommended.",
                      "ao": "Approximate texture-space result, not scene-baked AO."}}
    metadata_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    return [*outputs, metadata_path]
