# NEXUS Geospatial Engine & Spatial Analysis Architecture

## 1. Purpose & Phase Boundary
The NEXUS Geospatial Engine provides a reusable, unified spatial computation layer for point, line, polygon, road graph, and disaster hazard geometries. 

As established in Phase 06:
- It serves as the foundational geometric computation layer for emergency response.
- It encapsulates coordinate validation, CRS reprojection, geodesic distance, metric buffering, spatial predicates, spatial joins, proximity, and GeoJSON serialization.
- **Explicit Boundary**: It does **NOT** implement Dijkstra, A*, routing algorithms, dynamic rerouting, hydrodynamic flood simulation, or ML risk models. Those belong to later phases.

---

## 2. Coordinate System & Convention
- **Canonical Geographic CRS**: `WGS84` (`EPSG:4326`).
- **Coordinate Tuple Convention**: Standard GeoJSON `[longitude, latitude]` (`[X, Y]`).
- **Validation Rules**:
  - Longitude $\in [-180.0, 180.0]$
  - Latitude $\in [-90.0, 90.0]$
  - Coordinates must be finite numbers (no `NaN`, no `inf`).
  - Strict domain errors (`InvalidCoordinateError`, `InvalidGeometryError`) are raised upon violation.

---

## 3. Projection Strategy & Local Metric UTM
Geographic coordinates in `EPSG:4326` express positions in angular degrees. Computing buffers, lengths, or areas directly using degree math introduces severe distortion and spatial errors.

### Reprojection Strategy:
1. When metric operations are required (e.g. buffering in meters, polygon area in $\text{m}^2$, line length in meters), the engine computes the centroid of the feature in WGS84.
2. The engine calculates the corresponding Universal Transverse Mercator (UTM) zone:
   $$\text{Zone} = \left\lfloor \frac{\text{lon} + 180.0}{6.0} \right\rfloor + 1$$
   - Northern hemisphere: `EPSG:32600 + Zone`
   - Southern hemisphere: `EPSG:32700 + Zone`
3. The geometry is reprojected via `pyproj.Transformer(always_xy=True)` to the local metric UTM projection.
4. Metric planar operations are executed with zero angular distortion.
5. The result is reprojected back to canonical `EPSG:4326`.

---

## 4. Geometry Operations Implemented

| Operation | Module | Description |
| :--- | :--- | :--- |
| **Validation** | `geospatial.spatial_analysis.validation` | Validates coordinate bounds, non-empty geometries, and topological validity. |
| **Transform** | `geospatial.spatial_analysis.transform` | Dynamic UTM zone lookup, deterministic reprojection between WGS84 and projected CRSs. |
| **Distance** | `geospatial.spatial_analysis.distance` | Great-circle Haversine formula for coordinates/points; UTM planar distance for point-to-line/polygon. |
| **Buffer** | `geospatial.spatial_analysis.buffer` | True metric buffering in meters via local UTM projection with positive distance enforcement. |
| **Predicates** | `geospatial.spatial_analysis.predicates` | `intersects`, `intersection_geometry` (clipping), `batch_intersects`, `contains`, `within`, `covers`. |
| **Proximity** | `geospatial.spatial_analysis.proximity` | `find_within_distance` and `nearest_feature` with deterministic sorting and tie-breaking. |
| **Length & Area**| `geospatial.spatial_analysis.distance` | True metric `geometry_length_meters` and `polygon_area_sq_meters`. |
| **GeoJSON** | `geospatial.spatial_analysis.geojson` | Seamless conversion between Shapely geometries and GeoJSON dictionaries/FeatureCollections. |

---

## 5. PostGIS vs. Python Responsibility Split

NEXUS establishes a clear operational separation between application-side Python geometry computation and database-side PostGIS spatial operations:

| Task / Responsibility | Primary Engine | Rationale |
| :--- | :--- | :--- |
| **Offline Ingestion & Normalization** | Python (`geospatial.spatial_analysis`) | Runs offline or in worker pipelines without database dependencies. |
| **Road Graph Geometry Processing** | Python (`geospatial.osm`) | Graph construction and geometric validation in memory. |
| **Local Fixtures & Unit Tests** | Python (`shapely`, `pyproj`) | Fully testable without active Docker/DB services. |
| **Spatial Indexing (GiST)** | PostGIS (`PostgreSQL 16 + PostGIS 3.4`) | High-concurrency spatial indexing across millions of nodes/ways. |
| **Large-scale Spatial Joins** | PostGIS (`ST_Intersects`, `ST_DWithin`) | Pushes heavy spatial joins to the database engine. |
| **Database Coordinate Transformations** | PostGIS (`ST_Transform`) | Enables spatial queries across differing projected coordinate spaces on the DB server. |

---

## 6. Domain Foundations (Elevation, Rainfall, Flood, Population, Vulnerability)
- **Elevation** (`geospatial/elevation`): Exposes `get_elevation(point)` interface. Marked unconfigured until SRTM/Copernicus DEM data source is integrated. Returns `None`. No fabricated elevation values.
- **Rainfall** (`geospatial/rainfall`): Exposes `get_rainfall(location, timestamp)`. Marked unconfigured. Returns `None`. No synthetic rainfall readings.
- **Flood** (`geospatial/flood`): Defines `FloodExtent` data contract, polygon area calculation, and exposed road length calculation (`calculate_exposed_length`). Does not implement hydrodynamic simulation.
- **Population** (`geospatial/population`): Defines `PopulationZone` spatial model.
- **Vulnerability** (`geospatial/vulnerability`): Defines `VulnerableAsset` spatial model for elderly, healthcare, and mobility assets.

---

## 7. Limitations & Future Work
1. **Antimeridian Crossing**: Geometries spanning the $\pm 180^\circ$ meridian require splitting prior to single-zone UTM projection.
2. **Polar Projections**: UTM is defined between $80^\circ\text{S}$ and $84^\circ\text{N}$. For polar regions, UPS (Universal Polar Stereographic) should be utilized.
3. **Emergency Routing**: Deliberately deferred to subsequent phases.
