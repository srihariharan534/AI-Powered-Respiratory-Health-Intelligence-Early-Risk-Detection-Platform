# NEXUS Data Contracts Architecture

This document establishes the canonical data contracts, coordinate reference standards, enumeration vocabularies, and validation flow for the NEXUS platform.

---

## 1. The Canonical Contract Principle

No subsystem in NEXUS may invent internal, incompatible variations of core emergency domain data:

```text
RAW SOURCE (OSM, Sensors, Field Officers, SMS)
      ↓
NORMALIZATION PIPELINE
      ↓
CANONICAL DATA CONTRACT (JSON Schema / Pydantic)
      ↓
VALIDATION GATE
      ↓
DIGITAL TWIN / SPATIAL DATABASE / ROUTING ENGINE / FIELD PWA
```

---

## 2. Established Contracts

The canonical contracts are versioned and stored under `data/schemas/`:

1. **Incident Contract** (`incident.schema.json` / `Incident`):
   - Emergency observations, water inundation reports, trapped individuals, and infrastructure distress.
   - Controlled severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and status (`OPEN`, `ACKNOWLEDGED`, `IN_PROGRESS`, `RESOLVED`, `CANCELLED`).
2. **Road & Bridge Contract** (`road.schema.json` / `Road`):
   - Road network links, highway tiers, and bridge status (`OPEN`, `RESTRICTED`, `BLOCKED`, `UNKNOWN`).
3. **Hospital Contract** (`hospital.schema.json` / `Hospital`):
   - Medical triage facilities, bed/ICU availability, emergency intake status, and accessibility.
4. **Shelter Contract** (`shelter.schema.json` / `Shelter`):
   - Relief camps, emergency shelter capacity, potable water, and backup power availability.
5. **Recommendation Contract** (`recommendation.schema.json` / `Recommendation`):
   - Decision intelligence directives. **Mandates human coordinator sign-off** (`requires_human_approval: true`), factors attribution, and calibrated uncertainty bounds.
6. **SMS Fallback Contract** (`sms.schema.json` / `SMSMessage`):
   - Space-delimited field messages parsed into structured emergency payloads.

---

## 3. Spatial & Geographic Standards

- **Standard**: WGS 84 (`EPSG:4326`).
- **Coordinate Order Rule**: GeoJSON standard `[longitude, latitude]` must be strictly followed across all JSON payloads.
- **Bounds**:
  - `longitude`: $[-180.0, 180.0]$
  - `latitude`: $[-90.0, 90.0]$

---

## 4. Human-in-the-Loop & Confidence Integrity

- Every recommendation must enforce `requires_human_approval: true`.
- Confidence values, when present, must fall strictly in $[0.0, 1.0]$.
- **Rule**: Metrics are produced only by executable models. No synthetic or fabricated confidence values are permitted.
