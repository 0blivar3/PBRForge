import numpy as np
from exporter.exporter import export_maps

def test_export_creates_textures_and_metadata(tmp_path):
    source = np.zeros((8, 8, 3), dtype=np.uint8)
    result = export_maps(tmp_path, "Stone", source, {"height": np.ones((8, 8), dtype=np.uint8)})
    assert (tmp_path / "Stone_Albedo.png").exists()
    assert (tmp_path / "Stone_Height.png").exists()
    assert (tmp_path / "MaterialInfo.json").exists()
    assert len(result) == 3
