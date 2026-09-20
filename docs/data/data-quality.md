# NEXUS Data Quality Rules

This specification establishes data validation criteria, quality gates, missing-data policies, and synthetic labeling standards.

---

## 1. Core Data Quality Gates

All data entering the authoritative Digital Twin or PostgreSQL storage must pass through three verification filters:

1. **Syntactic Validation**: Valid UTF-8 JSON matching official JSON Schema draft 2020-12.
2. **Schema Invariant Enforcement**:
   - `available_capacity <= total_capacity`.
   - Coordinates strictly bounded by $[-180, 180]$ and $[-90, 90]$ with `[longitude, latitude]` ordering.
   - Priority integers constrained to $[1, 5]$.
   - ISO-8601 UTC timestamps with timezone designations.
3. **Semantic Provenance**:
   - Every ingested entity must carry an explicit `source` tag referencing a verified source in `data/provenance/sources.yaml`.

---

## 2. OpenStreetMap Quality Verification (Phase 05)

- **Geometry**: Must be valid LineString or MultiLineString geometries with $\ge 2$ vertices. Coordinates must fall within legitimate geographic bounding boxes.
- **Node & Edge Invariants**: Every graph edge must refer to existing `source_node` and `target_node` identifiers.
- **Directionality**: One-way flags (`oneway=yes` or `oneway=-1`) must emit correctly oriented directed edges without spurious opposing paths.
- **Geodesic Distance**: Edge lengths must be strictly non-negative and computed in meters using great-circle distance.
- **Bridges**: Every detected bridge feature must retain its parent `road_id` foreign reference for simulated structural failure propagation.

---

## 3. Missing & Uncertain Data Handling

- Critical identifiers (`id`), status enumerations, and coordinates cannot be null or omitted.
- Optional sensor attributes (e.g. `water_depth_cm`, `speed_limit_kmh`) default to `null` if unmeasured.
- Subsystems must not assume missing values imply zero risk (e.g. absent water depth measurement does not imply dry pavement).

---

## 4. Synthetic vs. Live Data Guardrail

- Any test or demonstration fixture must be tagged with `source: synthetic_demo`.
- Mock or simulated events must never be masqueraded as real-time disaster alerts.
