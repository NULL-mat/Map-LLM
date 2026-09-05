"""Stable vector data readers for local GIS files."""

from pathlib import Path
from typing import Any

import fiona
import geopandas as gpd
from shapely.geometry import shape


def read_vector_file(file_path: str | Path, **kwargs: Any) -> gpd.GeoDataFrame:
    """Read vector data without GeoPandas' Fiona feature conversion path.

    On some customer machines, ``GeoDataFrame.from_features`` triggers a Fiona
    ``__geo_interface__`` bug.  Reading feature properties and coordinates
    manually avoids that conversion layer while still using Fiona/GDAL for IO.
    """
    try:
        return _read_with_fiona_manual(file_path, **kwargs)
    except Exception:
        fallback_kwargs = dict(kwargs)
        fallback_kwargs.setdefault("engine", "fiona")
        return gpd.read_file(file_path, **fallback_kwargs)


def _read_with_fiona_manual(file_path: str | Path, **kwargs: Any) -> gpd.GeoDataFrame:
    open_kwargs = dict(kwargs)
    open_kwargs.pop("engine", None)

    records: list[dict[str, Any]] = []
    geometries = []

    with fiona.open(file_path, **open_kwargs) as source:
        crs = source.crs_wkt or source.crs
        for feature in source:
            records.append(_feature_properties(feature))
            geometry_mapping = _geometry_mapping(getattr(feature, "geometry", None))
            geometries.append(shape(geometry_mapping) if geometry_mapping else None)

    return gpd.GeoDataFrame(records, geometry=geometries, crs=crs)


def _feature_properties(feature) -> dict[str, Any]:
    properties = getattr(feature, "properties", None)
    if properties is None and isinstance(feature, dict):
        properties = feature.get("properties")

    if properties is None:
        return {}
    if hasattr(properties, "items"):
        return dict(properties.items())
    return dict(properties)


def _geometry_mapping(geometry) -> dict[str, Any] | None:
    if geometry is None:
        return None
    if isinstance(geometry, dict):
        return geometry

    geometry_type = getattr(geometry, "type", None)
    if geometry_type is None:
        return None

    if geometry_type == "GeometryCollection":
        children = getattr(geometry, "geometries", None) or []
        return {
            "type": geometry_type,
            "geometries": [
                child_mapping
                for child in children
                if (child_mapping := _geometry_mapping(child)) is not None
            ],
        }

    coordinates = getattr(geometry, "coordinates", None)
    if coordinates is None:
        return None
    return {"type": geometry_type, "coordinates": coordinates}
