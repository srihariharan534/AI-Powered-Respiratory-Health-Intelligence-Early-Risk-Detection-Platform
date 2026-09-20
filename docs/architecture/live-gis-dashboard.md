# NEXUS Live GIS Dashboard Architecture

## 1. Overview & Phase Scope

The **Live GIS Command Center Dashboard** is the primary operational surface of the NEXUS Platform. Built in **Phase 13**, it integrates existing capabilities across:
- **Phase 05**: OpenStreetMap Road Graph & Bridge entities
- **Phase 06**: Geospatial Engine (`WGS84`, metric transformations, geodesic calculations)
- **Phase 07**: Emergency Routing (A* / Dijkstra optimal paths)
- **Phase 08**: Dynamic Rerouting (operational state overlay, route invalidation, and diversion explanation)
- **Phase 09**: Digital Twin (versioned operational state authority)
- **Phase 10**: Flood Inundation Simulation (scenario polygons and depth exposure)
- **Phase 11**: What-If Scenarios (isolated counterfactual simulation without mutating live state)
- **Phase 12**: Command Center Shell, accessible primitives, and routing

---

## 2. Core Visual & Decision Hierarchy

The interface operational hierarchy follows:
```text
RISK
  ↓
DECISION
  ↓
ACTION
  ↓
CHANGE
```

1. **Map-First Operational Surface**: The GIS map is the dominant component of the Command Center, surrounded by restrained telemetry indicators and a responsive contextual detail inspector.
2. **Honest Data Provenance & Unambiguous Modes**: 
   - Real operational data and simulation scenarios are visually distinct.
   - Simulation layers feature dashed borders and explicit `SIMULATION` watermarks.
   - Zero fake risk scores or fabricated "AI lives saved" metrics.

---

## 3. Map Technology & GeoJSON Conventions

- **Mapping Library**: Leaflet with CartoDB Dark Matter tile service.
- **Coordinate Conventions**: Standard GeoJSON `[longitude, latitude]` (`EPSG:4326` / WGS84).
- **Coordinate Conversion**: Safely transposed to Leaflet's `[latitude, longitude]` during vector rendering.
- **Validation**: Strict geometry and ring coordinate checking prevents map crashing from malformed server features.

---

## 4. Operational Layers & Symbology

| Layer | Symbology | Source / Integration |
|---|---|---|
| **Flood Hazard** | Red / Amber translucent polygons with dashed borders in simulation | Phase 10 Flood Simulation Engine |
| **Roads** | Green solid lines (Open) vs Red dashed lines (Blocked/Flooded) | Phase 05 OSM Graph + Phase 08 State Overlay |
| **Dynamic Routes** | Blue solid line (Active Detour) vs Red dashed line (Invalidated) | Phase 07 / Phase 08 Dynamic Rerouter |
| **Bridges** | Slate / Red circular nodes indicating clearance & failure | Phase 08 / Phase 09 Digital Twin |
| **Incidents** | Severity-coded circular markers (Critical, High, Medium) | Phase 04 Incident Contracts |
| **Facilities** | Cross icons for Hospitals (✚) and Tent icons for Shelters (⛺) | Phase 04 Facility Schemas |

---

## 5. Dynamic Rerouting Visualization

When bridge or road status changes invalidate a route, the dashboard displays:
- The invalidated corridor marked with dashed red lines.
- The active diversion computed by the dynamic rerouter in solid blue.
- The **Dynamic Rerouting Advisory** panel detailing:
  - Detour distance delta ($+1.4\text{ km}$)
  - Travel delay delta ($+2.7\text{ min}$)
  - Natural language route change explanation

---

## 6. Testing & Quality Assurance

- **Unit & Component Testing**: 16 unit tests covering UI primitives, layout navigation, API client failure modes, map controls, legend symbology, and detail panel inspection.
- **Production Build**: Verified with TypeScript (`tsc`) and Vite (`npm run build`).
- **Regression Suite**: 131 tests passing in `tests/` validating full backend integrity.
