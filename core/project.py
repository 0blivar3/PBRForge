from __future__ import annotations
import io, json, zipfile
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from PIL import Image
PROJECT_VERSION = 1

def save_project(path: str | Path, source: np.ndarray, maps: dict[str, np.ndarray],
                 name: str, settings: dict | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"format": "PBRForge", "version": PROJECT_VERSION, "name": name,
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "settings": settings or {}, "maps": ["source", *sorted(maps.keys())]}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("project.json", json.dumps(manifest, indent=2))
        for key, array in {"source": source, **maps}.items():
            buffer = io.BytesIO()
            Image.fromarray(np.asarray(array).astype(np.uint8)).save(buffer, format="PNG")
            archive.writestr(f"textures/{key}.png", buffer.getvalue())

def load_project(path: str | Path) -> tuple[np.ndarray, dict[str, np.ndarray], dict]:
    with zipfile.ZipFile(path, "r") as archive:
        manifest = json.loads(archive.read("project.json"))
        if manifest.get("format") != "PBRForge" or manifest.get("version") != PROJECT_VERSION:
            raise ValueError("Unsupported or invalid PBRForge project")
        arrays = {}
        for key in manifest.get("maps", []):
            with Image.open(io.BytesIO(archive.read(f"textures/{key}.png"))) as image:
                arrays[key] = np.asarray(image.convert("RGBA" if "A" in image.getbands() else "RGB")).copy()
    if "source" not in arrays:
        raise ValueError("Project does not contain a source texture")
    source = arrays.pop("source")
    return source, arrays, manifest
