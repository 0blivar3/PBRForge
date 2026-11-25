import numpy as np
from core.project import save_project, load_project

def test_project_roundtrip(tmp_path):
    source = np.zeros((8, 9, 3), dtype=np.uint8)
    height = np.full((8, 9), 127, dtype=np.uint8)
    path = tmp_path / "test.pbrforge"
    save_project(path, source, {"height": height}, "Test")
    loaded_source, maps, manifest = load_project(path)
    assert np.array_equal(source, loaded_source)
    assert np.array_equal(height, maps["height"])
    assert manifest["name"] == "Test"
