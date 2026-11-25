# PBRForge

**PBRForge** is an open-source desktop tool for authoring game-ready PBR texture sets.

## First milestone — working MVP

- Import PNG, JPEG, BMP, TIFF, TGA and WebP source textures.
- Procedural Height generation: luminance, grayscale, edge and combined modes.
- Tangent-space Normal Map generation from source-derived or generated height.
- OpenGL (Y+) and DirectX (Y−) normal-map conventions.
- Procedural Roughness estimation with brightness, detail and local-contrast methods in the generator API.
- 2D texture preview.
- Portable .pbrforge project archives.
- PNG, TGA and TIFF texture export with a MaterialInfo.json manifest.
- Background generation worker to keep image processing off the GUI thread.

> Procedural Roughness is an editable estimate, not physically measured material data. Review and adjust generated maps artistically.

## Requirements

- Python 3.12+
- Windows 10/11 (the application code is cross-platform and can also run on macOS/Linux)

## Install

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Tests

```bash
pytest -q
```

A .pbrforge file is a ZIP archive containing a versioned JSON manifest and PNG texture resources. The source image is stored separately from generated maps.

## Roadmap

This is the first implementation milestone, not a claim that all long-term features are complete. Metallic/AO/Opacity generation, painting, undo/redo, interactive 3D PBR preview, channel packing, seamless tools, batch processing and engine profiles are planned for subsequent milestones.
