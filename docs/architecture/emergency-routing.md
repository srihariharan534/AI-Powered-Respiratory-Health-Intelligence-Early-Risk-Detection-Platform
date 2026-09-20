# NEXUS Emergency Routing Engine Architecture

## 1. Purpose & Phase Boundary
The Emergency Routing Engine (`geospatial/routing/`) provides practical, deterministic shortest-path route computation across the NEXUS road network.

### Architectural Boundary:
- **Phase 07 Scope**: Operates on the validated Phase 05 OpenStreetMap (OSM) road graph topology and Phase 06 Geospatial Engine. Respects road directionality, road status (`OPEN`, `RESTRICTED`, `BLOCKED`, `UNKNOWN`), accessibility categories, and emergency vehicle constraints. Provides distance and travel-time minimization.
- **Strict Boundary**: Does **NOT** implement dynamic rerouting, real-time flood simulation, or ML recommendations. Those capabilities belong to subsequent phases.

---

## 2. Core Routing Pipeline

```text
Origin Coordinate [lon, lat]          Destination Coordinate [lon, lat]
          ↓                                        ↓
  Snap to Nearest Node                     Snap to Nearest Node
          \                                        /
           \                                      /
            ↓                                    ↓
            RoutingGraphAdapter (Phase 05 Graph)
                            ↓
             Traversability & Policy Constraints
                            ↓
                   Cost Calculation
             (Distance or Travel Time)
                            ↓
                Shortest-Path Solver
                (Dijkstra / A* Search)
                            ↓
            Route Reconstruction & GeoJSON
```

---

## 3. Key Components & Implementation

### 3.1 Graph Adapter (`geospatial.routing.road_graph`)
The `RoutingGraphAdapter` wraps the NetworkX `MultiDiGraph` and `RoadGraphDefinition` from Phase 05:
- Decouples routing algorithms from raw OSM element parsing.
- Exposes node queries (`get_nodes`, `get_node_coordinates`, `get_successors`).
- Exposes edge queries (`get_edges_between`, `get_edge_by_id`) with edge attributes (`length_meters`, `road_type`, `speed_limit_kmh`, `status`, `accessibility`).

### 3.2 Nearest-Node Snapping (`geospatial.routing.nearest_node`)
- Snaps geographic coordinates `[longitude, latitude]` to the closest road network node.
- Uses geodesic great-circle Haversine calculations from Phase 06 (`geospatial.spatial_analysis.distance.distance_meters`).
- Employs deterministic lexicographical tie-breaking for equal-distance candidate nodes.
- Rejects requests when coordinates fall beyond `max_search_radius_meters`.

### 3.3 Traversal Constraints & Policy (`geospatial.routing.constraints`)
The `EmergencyRoutingPolicy` regulates traversability:
- **Road Status**:
  - `OPEN`: Traversable.
  - `RESTRICTED`: Traversable with optional penalty multiplier if `allow_restricted_roads=True`.
  - `BLOCKED`: Impassable (avoided completely).
  - `UNKNOWN`: Controlled by `allow_unknown_roads`.
- **Accessibility & Vehicle Type**:
  - `EMERGENCY_ONLY`: Traversable by authorized emergency response vehicles.
  - `HIGH_CLEARANCE_ONLY`: Blocked for standard low-clearance ambulances; accessible to heavy rescue and fire apparatus.
  - `IMPASSABLE`: Rejected for all vehicles.
  - `access=private`: Governed by `allow_private_roads`.

### 3.4 Edge Cost & Speed Modeling (`geospatial.routing.costs`)
Supports two operational objectives:
1. **Distance Mode (`RoutingMode.DISTANCE`)**:
   - Cost is the edge length in meters.
2. **Travel-Time Mode (`RoutingMode.TRAVEL_TIME`)**:
   - Cost is estimated duration in seconds: $\text{duration} = \frac{\text{length}}{\text{speed}}$.
   - Uses explicit `speed_limit_kmh` where tagged in OSM data.
   - Falls back to documented, conservative urban speed defaults when `maxspeed` is missing:
     - `motorway`: 80 km/h
     - `trunk`: 60 km/h
     - `primary`: 50 km/h
     - `secondary`: 40 km/h
     - `tertiary`: 30 km/h
     - `residential`: 25 km/h
     - `service`: 15 km/h
     - `bridge`: 40 km/h
     - default fallback: 30 km/h

### 3.5 Solvers: Dijkstra & A* (`geospatial.routing.router`)
- **Dijkstra**: Guaranteed shortest-path calculation using min-heap priority queue with deterministic tie-breaking.
- **A* Search**: Uses an admissible geodesic heuristic:
  - In distance mode: Great-circle straight-line distance (never overestimates distance on Earth).
  - In travel-time mode: Straight-line distance divided by maximum permissible network speed ($120\text{ km/h} = 33.33\text{ m/s}$) (never overestimates travel time).

### 3.6 Route Geometry & GeoJSON Serialization (`geospatial.routing.route`, `serialization`)
- Reconstructs turn-by-turn road segments with individual metrics (`length_meters`, `duration_seconds`).
- Stitches continuous GeoJSON `LineString` coordinates without duplicate juncture points.
- Serializes to standard GeoJSON `Feature` and `FeatureCollection` formats.

---

## 4. Verification & Testing
Tested in `tests/geospatial/test_routing.py` across:
- Directionality enforcement (`oneway=yes` forward vs blocked reverse).
- Nearest node geographic snapping.
- Equivalence of Dijkstra and A* path results.
- Distance optimization vs travel-time optimization.
- Emergency vehicle accessibility permissions.
- Rejection of `BLOCKED` roads.
- Zero-length identity routing when origin and destination snap to the identical node.
- Full GeoJSON serialization.
