import numpy as np
from generators.height import generate_height
from generators.normal import generate_normal
from generators.roughness import generate_roughness

def test_height_preserves_dimensions_and_range():
    source = np.zeros((32, 48, 3), dtype=np.uint8)
    source[:, 24:] = 255
    result = generate_height(source)
    assert result.shape == (32, 48) and result.dtype == np.uint8
    assert result.min() == 0 and result.max() == 255

def test_flat_height_produces_neutral_normal():
    height = np.full((32, 32), 127, dtype=np.uint8)
    result = generate_normal(height)
    assert result.shape == (32, 32, 3)
    assert np.all(result[..., 0] == 128)
    assert np.all(result[..., 1] == 128)
    assert np.all(result[..., 2] == 255)

def test_directx_flips_green_channel():
    y, x = np.mgrid[0:32, 0:32]
    height = np.asarray(y * 8, dtype=np.uint8)
    gl = generate_normal(height, convention="opengl")
    dx = generate_normal(height, convention="directx")
    assert np.allclose(gl[..., 1].astype(int) + dx[..., 1].astype(int), 256, atol=1)

def test_roughness_is_grayscale():
    source = np.random.default_rng(4).integers(0, 256, (24, 24, 3), dtype=np.uint8)
    result = generate_roughness(source)
    assert result.shape == (24, 24) and result.dtype == np.uint8
