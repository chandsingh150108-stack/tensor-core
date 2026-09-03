"""Generate synthetic test fixtures for ingestion tests."""
import numpy as np
import struct


def create_pds3_binary():
    """Create a 64x64 uint16 PDS3 raw body."""
    rng = np.random.default_rng(42)
    img = rng.integers(100, 200, size=(64, 64), dtype=np.uint16)
    img.tofile("tests/fixtures/synth_pds3_body.img")
    print(f"Created synth_pds3_body.img: {img.shape}, min={img.min()}, max={img.max()}")


def create_pds4_binary():
    """Create a 64x64 uint16 PDS4 raw body."""
    rng = np.random.default_rng(42)
    img = rng.integers(100, 200, size=(64, 64), dtype=np.uint16)
    img.tofile("tests/fixtures/synth_pds4_body.img")
    print(f"Created synth_pds4_body.img: {img.shape}, min={img.min()}, max={img.max()}")


def create_geotiff():
    """Create a 64x64 synthetic GeoTIFF."""
    import rasterio
    from rasterio.transform import from_bounds

    rng = np.random.default_rng(42)
    img = rng.integers(100, 200, size=(64, 64), dtype=np.uint16)

    transform = from_bounds(0, 0, 320, 320, 64, 64)

    with rasterio.open(
        "tests/fixtures/synth_geotiff.tif",
        "w",
        driver="GTiff",
        height=64,
        width=64,
        count=1,
        dtype="uint16",
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(img, 1)
        dst.update_tags(SUN_AZIMUTH="150.0", SUN_ELEVATION="25.0")

    print(f"Created synth_geotiff.tif: {img.shape}, min={img.min()}, max={img.max()}")


if __name__ == "__main__":
    create_pds3_binary()
    create_pds4_binary()
    create_geotiff()
    print("All fixtures created.")
