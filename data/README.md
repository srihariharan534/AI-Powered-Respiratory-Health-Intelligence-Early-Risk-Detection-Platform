# NEXUS Data Layer

This directory hosts canonical data contracts, test sample fixtures, and dataset provenance registries for the NEXUS platform.

---

## 1. Directory Structure

- `data/schemas/`: Authoritative machine-readable JSON Schemas (Draft 2020-12) for all core domain entities.
- `data/sample/`: Small, deterministic synthetic fixtures used strictly for offline contract testing and schema verification.
- `data/provenance/`: Traceable registries documenting all external data sources, licensing obligations, and normalization transformations.

---

## 2. Canonical Contracts

| Contract | JSON Schema | Pydantic Model | Sample Fixture |
| :--- | :--- | :--- | :--- |
| **Incident** | `schemas/incident.schema.json` | `Incident` | `sample/incidents/sample_incident.json` |
| **Road** | `schemas/road.schema.json` | `Road` | `sample/roads/sample_road.json` |
| **Hospital** | `schemas/hospital.schema.json` | `Hospital` | `sample/hospitals/sample_hospital.json` |
| **Shelter** | `schemas/shelter.schema.json` | `Shelter` | `sample/shelters/sample_shelter.json` |
| **Recommendation**| `schemas/recommendation.schema.json`| `Recommendation` | `sample/recommendations/sample_recommendation.json` |
| **SMS** | `schemas/sms.schema.json` | `SMSMessage` | `sample/sms/sample_sms.json` |

---

## 3. Data Integrity & Provenance

- All external datasets are documented in `provenance/sources.yaml` with license terms in `provenance/licenses.yaml`.
- Data processing steps are logged in `provenance/transformations.yaml`.
- Test fixtures are explicitly marked `synthetic_demo` to distinguish them from real-world telemetry.

---

## 4. Geospatial Data Flow & Spatial Analysis

- Geospatial computations follow the WGS84 `EPSG:4326` standard with coordinates serialized as `[longitude, latitude]`.
- Reusable spatial operations (distance, buffering, intersections, proximity) reside under `geospatial/spatial_analysis/`.
- Elevation, rainfall, and population layers remain explicitly unconfigured until authoritative sources are acquired, preventing fabricated telemetry.
