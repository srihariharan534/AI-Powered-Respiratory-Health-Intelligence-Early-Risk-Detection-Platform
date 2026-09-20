# NEXUS OpenStreetMap Road Graph & Ingestion

This document details OpenStreetMap acquisition, highway normalization, bridge extraction, and directed topological graph generation for **Phase 05: OSM Road Graph**.

---

## 1. Role in NEXUS

OpenStreetMap provides the foundational real-world road graph topology for:
- Calculating baseline evacuation and dispatch routes (**Phase 07**).
- Dynamic edge invalidation upon flood submergence or bridge failure (**Phase 08**).
- Digital Twin physical infrastructure models (**Phase 09**).

> **Architectural Boundary Note**: The Phase 05 road graph is a structural topology foundation. It does not implement shortest-path routing, flood intersections, or dynamic recalculations.

---

## 2. Ingestion & Acquisition Pipeline

```text
OpenStreetMap Overpass API (scripts/fetch_data/fetch_osm.py)
      ↓ (Raw JSON Artifact)
data/raw/osm/osm_<place>_<timestamp>.json
      ↓ (Parsing & Filtering)
geospatial/osm/roads/parser.py (Extract OSMNode & OSMWay)
      ↓ (Tag & Attribute Normalization)
geospatial/osm/roads/normalizer.py (Canonical Road Contracts)
      ↓ (Topological Decomposition)
geospatial/osm/roads/graph_builder.py (Directed Edge Segments)
      ↓
NetworkX MultiDiGraph & RoadGraphDefinition
```

---

## 3. Tag Normalization Standards

| OSM Tag | Canonical Field | Normalization Rule |
| :--- | :--- | :--- |
| `highway` | `road_type` | Mapped to `motorway`, `primary`, `secondary`, `bridge`, etc. |
| `name` / `ref` | `name` | Extracted or defaulted to `Unnamed Road <way_id>`. |
| `maxspeed` | `speed_limit_kmh` | Converted to numeric km/h (mph converted via $\times 1.60934$). |
| `access` / `emergency` | `accessibility` | Evaluated into `ALL_VEHICLES`, `EMERGENCY_ONLY`, `IMPASSABLE`. |
| `oneway` | Edge Topology | `yes` (forward), `-1` (backward), `no` (bidirectional pairs). |
| `bridge` / `man_made=bridge` | `is_bridge` | Extracted into `BridgeEntity` associated via `road_id`. |

---

## 4. Road Operational Status

- Initial OSM ingest status defaults to `status = OPEN`.
- **Integrity Rule**: This represents a baseline structural property of the physical infrastructure, not real-time disaster status. Real-time road blockages are governed dynamically by field incident reports and the Digital Twin in subsequent phases.

---

## 5. Geodesic Calculations & Coordinate Ordering

- **Coordinate System**: WGS 84 (`EPSG:4326`).
- **Ordering**: strictly `[longitude, latitude]`.
- **Edge Lengths**: Calculated geodesically in meters using the Haversine formula (`geospatial/osm/roads/distance.py`) rather than planar Euclidean approximations.
