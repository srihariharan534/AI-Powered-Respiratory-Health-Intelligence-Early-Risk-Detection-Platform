# NEXUS Spatial Database Architecture

This document details the database architecture, spatial reference systems, and schema strategy established in **Phase 03: PostgreSQL + PostGIS**.

---

## 1. Database Role & Boundaries

NEXUS maintains a strict distinction between data layers:
- **PostgreSQL + PostGIS**: Authoritative central persistence layer for road network topologies, incident logs, medical/shelter facilities, and historical flood inundation masks.
- **Digital Twin**: Application-level in-memory state authority and state transition machine (**Phase 09**).
- **IndexedDB**: Browser/PWA client-side offline storage cache surviving network failure (**Phase 23**).

---

## 2. Spatial Reference Systems (SRS)

- **Storage & Ingestion**: `WGS 84` (`EPSG:4326`). Standard geographic coordinates (latitude, longitude) for interoperable GeoJSON, OpenStreetMap ingestion, and API payloads.
- **Metric Distance & Area Calculations**: For high-accuracy emergency routing distance and catchment buffer computations, spatial operations are projected to local UTM zones or use PostGIS `geography` type to eliminate planar distortion.

---

## 3. Schema Strategy

- Default schema: `public`.
- Extensions:
  - `postgis`: Core spatial types (`GEOMETRY`, `GEOGRAPHY`) and spatial indexing functions (`ST_DWithin`, `ST_Intersects`, `ST_Contains`).
- Migrations are version-controlled via Alembic under `infrastructure/database/migrations/`.

---

## 4. Future Domain Entities (Phases 04+)

The spatial schema will progressively model:
1. `Road` & `Bridge` (Phase 05: OSM Road Graph)
2. `FloodZone` (Phase 06: Geospatial Engine)
3. `Incident` (Phase 15: Incident Management)
4. `Hospital` & `Shelter` (Phase 16: Hospitals + Shelters)
5. `VulnerabilityIndex` (Phase 27: Vulnerability Prioritization)

Tables are introduced in their respective functional phases to prevent premature schema locking.
