# NEXUS Data Card

This document details dataset provenance, geographic coverage, known limitations, and licensing for all datasets in NEXUS.

---

## 1. Intended Scope & Operating Context

NEXUS processes geospatial and environmental observations to generate flood risk assessments and safe emergency evacuation routing.

---

## 2. Dataset Inventory

| Dataset Identifier | Domain | Source / Provider | License | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `osm` | Roads / Bridges | OpenStreetMap Contributors | ODbL 1.0 | *Planned (Phase 05)* | Road network graph extraction |
| `srtm_dem` | Elevation / Slope | NASA / USGS | US Public Domain | *Planned (Phase 06)* | 30m digital elevation grid |
| `historical_flood_catalog` | Historical Inundation | State Disaster Management Agency | Open Govt License | *Planned (Phase 28)* | Validation and backtesting |
| `synthetic_demo_suite` | Scenario Fixtures | NEXUS Engineering Team | Apache-2.0 | **ACTIVE** | Deterministic Judge scenarios |
| `baseline_risk_training_catalog` | Environmental Risk Observations | NEXUS Engineering Team | Apache-2.0 | **ACTIVE (SYNTHETIC)** | Reference dataset for Phase 17 baseline logistic regression |

---

## 3. Known Limitations & Failure Modes

1. **OSM Coverage Asymmetry**: Rural or informal settlement road networks may lack detailed bridge width or surface tags. Fallback speed limits and conservative clearance bounds apply.
2. **DEM Resolution**: 30m SRTM DEM does not resolve micro-embankments or street curbs. Localized field reports take precedence over coarse elevation predictions.
3. **Connectivity Latency**: Field incident data may arrive hours after occurrence due to network outages; the Digital Twin maintains state timestamps and audit logs.
