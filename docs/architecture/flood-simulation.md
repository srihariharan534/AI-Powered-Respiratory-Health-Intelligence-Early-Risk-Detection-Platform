# NEXUS Flood Simulation Engine

## 1. Purpose & Core Objective
The NEXUS Flood Simulation Engine is a deterministic, explainable scenario simulation layer that answers:
> *"If flood conditions change according to this scenario, which geographic areas and infrastructure become affected?"*

It transforms environmental inputs and scenario hypotheses into spatial flood-state updates that feed into the **NEXUS Digital Twin (Phase 09)** and subsequently into **Emergency Routing (Phases 07/08)**.

---

## 2. Critical Safety Boundary: Simulation vs. Prediction
> **IMPORTANT ARCHITECTURAL RULE:**  
> NEXUS **never** presents a simulated scenario as a real-time prediction.  
> Every simulation artifact explicitly includes `mode = "SIMULATION"` or `mode = "TEST_FIXTURE"`.  
> Outputs are never labeled as `LIVE FLOOD`, `ACTUAL FLOOD`, or `PREDICTED FLOOD`.

> **Scientific / Modeling Scope:**  
> Phase 10 implements **scenario-based flood inundation simulation and spatial exposure analysis**. It is **not** a validated hydrodynamic flood forecasting system (e.g. 2D shallow water equation solver). It approximates inundation based on water levels, elevation differentials, or explicit scenario hazard extents.

---

## 3. Architecture & Data Flow

```text
               ┌────────────────────────┐
               │     FloodScenario      │
               │ (Water Level, Depth,   │
               │   Explicit Polygon)    │
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │  FloodSimulationEngine │
               │ (Elevation Inundation  │
               │  or Polygon Analysis)  │
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │  SimulatedFloodExtent  │
               │ (Geometry, Depth,      │
               │  Severity, Area)       │
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │    Exposure Engine     │
               │ (Roads, Bridges, Hosps,│
               │  Shelters, Incidents)  │
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │   Digital Twin Sync    │
               │   - FloodUpdatedEvent  │
               │   - RoadStatusChanged  │
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │ Phase 08 StateOverlay  │
               │  (Dynamic Rerouting)   │
               └────────────────────────┘
```

---

## 4. Scenario Model
Implemented in [`geospatial/flood/scenario.py`](file:///c:/Users/pabit/Downloads/NEXUS/geospatial/flood/scenario.py):
- `scenario_id`: Stable identifier (e.g. `scen-surge-plus-1m`).
- `name`: Human-readable label.
- `mode`: `SimulationMode.SIMULATION` or `SimulationMode.TEST_FIXTURE`.
- `scenario_type`:
  - `WATER_LEVEL`: Absolute water level relative to datum.
  - `DEPTH_INCREMENT`: Increment above baseline (e.g. $+1.0\text{ m}$).
  - `EXPLICIT_POLYGON`: Inundated region provided directly via GeoJSON Polygon/MultiPolygon.
- Configurable road closure parameters:
  - `road_closure_depth_threshold_m`: Default $0.3\text{ m}$.
  - `auto_close_roads`: Default `False` (prevents unverified automatic closures).

---

## 5. Inundation & Elevation Approximation
Implemented in [`geospatial/flood/model.py`](file:///c:/Users/pabit/Downloads/NEXUS/geospatial/flood/model.py):
- Inundation rule:
  $$\text{depth} = \text{water\_level} - \text{terrain\_elevation}$$
- Cells where $\text{depth} > 0.0$ are grouped, united into valid Shapely multipolygons, and validated against coordinate bounds.
- Negative depths are rejected; dry ground is represented with $\text{depth} = 0.0\text{ m}$ or no inundation.

---

## 6. Severity Classification
Implemented in [`geospatial/flood/thresholds.py`](file:///c:/Users/pabit/Downloads/NEXUS/geospatial/flood/thresholds.py):
Configurable scenario thresholds (default NEXUS scenario values):
| Depth Range | Severity | Description |
| :--- | :--- | :--- |
| $[0.0\text{ m}, 0.3\text{ m}]$ | **LOW** | Minor street water; passable by emergency/high-clearance vehicles |
| $(0.3\text{ m}, 1.0\text{ m}]$ | **MODERATE** | Impassable to standard civilian vehicles; ground floor threat |
| $(1.0\text{ m}, 2.0\text{ m}]$ | **SEVERE** | Severe structural inundation; boats/air evacuation required |
| $> 2.0\text{ m}$ | **EXTREME** | Multi-story submersion; catastrophic hazard |

---

## 7. Spatial Exposure Analysis
Implemented in [`geospatial/flood/exposure.py`](file:///c:/Users/pabit/Downloads/NEXUS/geospatial/flood/exposure.py):
- **Road Exposure**: Evaluates geometric line intersection (`road_geom` $\cap$ `flood_geom`), computes submerged length in meters, and extracts flood depth.
- **Road Closure Rule**: Intersection does **not** automatically mark a road as `BLOCKED` unless `auto_close_roads = True` and $\text{depth} \ge \text{road\_closure\_depth\_threshold\_m}$.
- **Facility Exposure**: Checks point intersections for Hospitals, Shelters, Bridges, and Incidents without automatically claiming structural collapse or closure.

---

## 8. Scenario Comparison
Implemented in [`geospatial/flood/comparison.py`](file:///c:/Users/pabit/Downloads/NEXUS/geospatial/flood/comparison.py):
- Evaluates spatial symmetric difference ($\text{Scenario} \setminus \text{Baseline}$).
- Returns `newly_flooded_area_sq_meters`, `newly_affected_roads`, and newly affected facilities for comparative decision support.

---

## 9. Digital Twin & Phase 08 Dynamic Routing Integration
1. Simulation output generates `FloodUpdatedEvent`.
2. Digital Twin ingests event $\to$ increments `state_version`.
3. If road closure criteria are met, generates causal `RoadStatusChangedEvent(new_status=BLOCKED)`.
4. Digital Twin state manager synchronously updates Phase 08 `StateOverlay`.
5. Existing routes intersecting the blocked road are invalidated and dynamic rerouting is triggered.
