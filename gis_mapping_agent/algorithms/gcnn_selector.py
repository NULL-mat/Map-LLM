"""Public GCNN integration boundary.

The public repository documents the contract used by the road-generalization
pipeline, but does not distribute company data, trained weights, or inference
code.  The private deployment can provide a compatible selector implementation
through this module without changing the surrounding Agent and tool layers.
"""

from __future__ import annotations

from typing import Optional

import geopandas as gpd


class GCNNSelector:
    """Interface for an optional, privately supplied GCNN selector."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def select_by_gcnn(
        self,
        gdf: gpd.GeoDataFrame,
        data_dir: str,
        keep_ratio: Optional[float] = 1.0,
    ) -> gpd.GeoDataFrame:
        """Run the private selector when it is installed in the deployment.

        The public build deliberately fails closed instead of silently applying
        a different algorithm.  This keeps the advertised tool contract while
        preventing proprietary weights or training data from being inferred
        from the public repository.
        """

        raise RuntimeError(
            "GCNN implementation is not bundled in the public showcase. "
            "Configure the private deployment adapter to enable this algorithm."
        )
