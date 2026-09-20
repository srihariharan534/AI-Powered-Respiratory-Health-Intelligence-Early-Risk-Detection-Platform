"""
NEXUS Flood Simulation - Core Inundation Model.
Executes scenario-based flood inundation simulation and elevation-based approximation.
"""

from typing import List, Optional

import numpy as np
from shapely.geometry import Polygon, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from geospatial.flood.extent import SimulatedFloodExtent
from geospatial.flood.scenario import FloodScenario, ScenarioType
from geospatial.spatial_analysis.validation import validate_geometry


class ElevationGrid:
    """
    In-memory regular elevation raster grid for deterministic scenario modeling.
    Represents synthetic terrain or local elevation surfaces.
    """

    def __init__(
        self,
        elevations: np.ndarray,
        min_lon: float,
        min_lat: float,
        cell_size_deg: float,
    ) -> None:
        """
        elevations: 2D array of shape (rows, cols) representing terrain elevation in meters.
        min_lon, min_lat: Bottom-left coordinate.
        cell_size_deg: Spatial resolution in degrees.
        """
        if elevations.ndim != 2:
            raise ValueError("Elevations must be a 2D array")
        self.elevations = elevations
        self.rows, self.cols = elevations.shape
        self.min_lon = min_lon
        self.min_lat = min_lat
        self.cell_size = cell_size_deg

    def cell_polygon(self, r: int, c: int) -> Polygon:
        """Returns the bounding polygon for grid cell (r, c)."""
        # r: 0 is bottom (min_lat), increasing northward
        lon0 = self.min_lon + c * self.cell_size
        lat0 = self.min_lat + r * self.cell_size
        lon1 = lon0 + self.cell_size
        lat1 = lat0 + self.cell_size
        return Polygon([[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]])


class FloodSimulationEngine:
    """
    NEXUS Flood Simulation Engine.
    Executes scenario-based flood inundation simulation.
    Explicitly documented as SCENARIO-BASED INUNDATION APPROXIMATION, NOT A HYDRODYNAMIC MODEL.
    """

    def __init__(self, elevation_grid: Optional[ElevationGrid] = None) -> None:
        self.elevation_grid = elevation_grid

    def simulate(self, scenario: FloodScenario) -> SimulatedFloodExtent:
        """
        Execute simulation for the given FloodScenario:
        - If EXPLICIT_POLYGON: Uses supplied polygon directly with explicit/inferred depth.
        - If WATER_LEVEL or DEPTH_INCREMENT: Evaluates inundation against elevation grid.
        """
        if scenario.scenario_type == ScenarioType.EXPLICIT_POLYGON:
            return self._simulate_explicit_polygon(scenario)
        elif scenario.scenario_type in (ScenarioType.WATER_LEVEL, ScenarioType.DEPTH_INCREMENT):
            return self._simulate_elevation_inundation(scenario)
        else:
            raise ValueError(f"Unsupported scenario type: {scenario.scenario_type}")

    def _simulate_explicit_polygon(self, scenario: FloodScenario) -> SimulatedFloodExtent:
        assert scenario.flood_polygon is not None
        geom: BaseGeometry = shape(scenario.flood_polygon)
        validate_geometry(geom)

        depth = scenario.explicit_depth_m
        return SimulatedFloodExtent.from_shapely(
            flood_zone_id=f"FZ-{scenario.scenario_id}",
            scenario_id=scenario.scenario_id,
            geometry=geom,
            max_depth_m=depth,
            mean_depth_m=depth,
            mode=scenario.mode,
            source=scenario.source,
            metadata={
                "scenario_name": scenario.name,
                "model_type": "EXPLICIT_POLYGON_APPROXIMATION",
            },
        )

    def _simulate_elevation_inundation(self, scenario: FloodScenario) -> SimulatedFloodExtent:
        if self.elevation_grid is None:
            raise ValueError(
                f"Cannot execute {scenario.scenario_type} scenario: No elevation grid supplied to FloodSimulationEngine"
            )

        target_water_level = scenario.get_effective_water_level()
        if target_water_level is None:
            raise ValueError("Unable to determine effective water level from scenario")

        grid = self.elevation_grid
        # Inundation rule: depth = water_level - terrain_elevation
        depths = target_water_level - grid.elevations
        inundated_mask = depths > 0.0

        if not np.any(inundated_mask):
            # Empty inundation
            empty_poly = Polygon()
            return SimulatedFloodExtent.from_shapely(
                flood_zone_id=f"FZ-{scenario.scenario_id}",
                scenario_id=scenario.scenario_id,
                geometry=empty_poly,
                max_depth_m=0.0,
                mean_depth_m=0.0,
                mode=scenario.mode,
                source=scenario.source,
                metadata={"inundated_cells": 0},
            )

        # Collect inundated cell polygons and calculate depth metrics
        inundated_cells: List[Polygon] = []
        positive_depths: List[float] = []

        for r in range(grid.rows):
            for c in range(grid.cols):
                if inundated_mask[r, c]:
                    cell_poly = grid.cell_polygon(r, c)
                    inundated_cells.append(cell_poly)
                    positive_depths.append(float(depths[r, c]))

        merged_geom = unary_union(inundated_cells)
        validate_geometry(merged_geom)

        max_depth = float(np.max(positive_depths))
        mean_depth = float(np.mean(positive_depths))

        return SimulatedFloodExtent.from_shapely(
            flood_zone_id=f"FZ-{scenario.scenario_id}",
            scenario_id=scenario.scenario_id,
            geometry=merged_geom,
            max_depth_m=max_depth,
            mean_depth_m=mean_depth,
            mode=scenario.mode,
            source=scenario.source,
            metadata={
                "scenario_name": scenario.name,
                "target_water_level_m": target_water_level,
                "inundated_cells": int(np.sum(inundated_mask)),
                "model_type": "SCENARIO_INUNDATION_ELEVATION_APPROXIMATION",
            },
        )
