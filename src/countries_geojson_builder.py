from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
import geopandas as gpd
import requests

# Prefer the NACIS CDN (stable), then fall back to Natural Earth site
NE_ZIP_URLS = [
    "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip",
    "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_countries.zip",
]
SHAPEFILE_NAME = "ne_10m_admin_0_countries.shp"
DEFAULT_SIMPLIFY_TOLERANCE_KM = 25.0  # roughly 1:110m detail


def ensure_countries_geojson(
    geometry_dir: Path | None = None, *, simplify_tolerance_km: float = DEFAULT_SIMPLIFY_TOLERANCE_KM
) -> Path:
    """
    Ensure geometry/countries.geojson exists.
    If missing, download the Natural Earth countries shapefile, simplify it, and write GeoJSON.
    """
    base_dir = geometry_dir or Path(__file__).parent.parent / "geometry"
    target_geojson = base_dir / "countries.geojson"

    if target_geojson.exists():
        return target_geojson

    base_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        zip_path = tmp_path / "ne_countries.zip"
        download_zip(NE_ZIP_URLS[0], zip_path)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_path)

        shapefile_path = next(tmp_path.rglob(SHAPEFILE_NAME), None)
        if shapefile_path is None:
            raise FileNotFoundError(f"Could not find {SHAPEFILE_NAME} in extracted archive")

        gdf = gpd.read_file(shapefile_path)

        keep_cols = [col for col in ("ADMIN", "ADM0_A3", "ISO_A2", "ISO_A3", "CONTINENT") if col in gdf.columns]
        if keep_cols:
            gdf = gdf[keep_cols + ["geometry"]]

        gdf = simplify_for_country_lookup(gdf, tolerance_km=simplify_tolerance_km)
        gdf.to_file(target_geojson, driver="GeoJSON")

    return target_geojson


def download_zip(url: str, dest: Path) -> None:
    last_error: Exception | None = None
    for candidate in NE_ZIP_URLS:
        try:
            response = requests.get(candidate, stream=True, timeout=60, headers={"User-Agent": "whatsappbot/geojson"})
            response.raise_for_status()
            with dest.open("wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
            return
        except Exception as exc:  # noqa: BLE001 - want to capture any failure
            last_error = exc
            continue

    raise RuntimeError(f"Failed to download Natural Earth zip from {NE_ZIP_URLS}") from last_error


def simplify_for_country_lookup(gdf: gpd.GeoDataFrame, *, tolerance_km: float) -> gpd.GeoDataFrame:
    """
    Simplify polygons in a metric CRS so the GeoJSON is small but useful for point-in-country tests.
    """
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)

    gdf = gdf.to_crs(3857)
    simplified = gdf.geometry.simplify(tolerance=tolerance_km * 1000, preserve_topology=True)
    gdf = gdf.set_geometry(simplified).to_crs(4326)
    return gdf


if __name__ == "__main__":
    output = ensure_countries_geojson()
    print(f"Wrote {output}")
