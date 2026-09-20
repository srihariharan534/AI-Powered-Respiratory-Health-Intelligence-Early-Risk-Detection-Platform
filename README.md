# NEXUS — Offline-First AI Multi-Emergency Decision Intelligence Platform

> **Hazard-Agnostic Emergency Decision-Intelligence Platform**  
> Resilient, offline-first operational continuity, dynamic routing, resource optimization, and human-in-the-loop decision support under critical infrastructure failure across 12 disaster domains.

---

## 1. Problem Statement

During compound climate and municipal emergencies, emergency operations break down when communications fail, field reports arrive late or distorted, transport routes become severed without warning, and coordinators lack centralized situational awareness. Most contemporary disaster systems require continuous cloud connectivity and break under field conditions.

## 2. Solution Overview

NEXUS bridges field responders and the district command center across 12 emergency types:

```text
Emergency Domain (Flood, Cyclone, Wildfire, Landslide, Earthquake, Heat, etc.)
→ Hazard-Agnostic Core
→ Single Digital Twin Authority
→ Dynamic Emergency Routing
→ Offline Field PWA (IndexedDB + Outbox)
→ Durable Synchronization & Idempotency
→ What-If Scenario Simulation
→ Explainable Recommendation Engine
→ Constrained Resource Allocation
→ Counterfactual Multi-Criteria Trade-offs
→ Mandatory Human Approval
→ Immutable Chronological Audit Ledger
```

---

## 3. Current Project Status

```text
STATUS: PHASES 00–46 COMPLETE — FINAL SYSTEM FREEZE
SUPPORTED HAZARD DOMAINS: 12 Emergency Domains (Flood Validated + 11 Extensible Modules)
CORE PRINCIPLE: NEXUS recommends. An authorized human decides. The system records what happened.
```

NEXUS combines geospatial intelligence, multi-hazard risk analysis, dynamic routing, Digital Twin state, resilient field operations, what-if simulation, explainable recommendations, resource allocation, and human approval into one auditable operational decision loop.



---

## 4. System Requirements

- **Python**: 3.10+ (Tested on Python 3.11/3.13)
- **Node.js**: Current LTS (Node.js 20+, tracked via `.nvmrc`)
- **Package Manager**: `npm` or `pnpm`
- **Docker & Docker Compose**: Version 24+ / Compose v2
- **Database**: PostgreSQL 16 with PostGIS 3.4
- **Git**

Verify developer environment health:
```bash
make health-check
```

---

## 5. Development & Database Commands

The root `Makefile` provides standardized targets across development phases:

| Command | Status | Description |
| :--- | :--- | :--- |
| `make setup` | **AVAILABLE** | Installs Python development dependencies |
| `make dev` | **AVAILABLE** | Launches containerized development stack |
| `make test` | **AVAILABLE** | Runs unit and contract test suites via pytest |
| `make health-check` | **AVAILABLE** | Validates developer machine toolchain & config |
| `make db-up` | **AVAILABLE** | Starts PostgreSQL 16 + PostGIS 3.4 container |
| `make db-down` | **AVAILABLE** | Stops PostGIS database container |
| `make db-migrate` | **AVAILABLE** | Applies pending Alembic migrations |
| `make db-status` | **AVAILABLE** | Validates database connectivity and PostGIS version |
| `make db-reset` | **AVAILABLE** | [CAUTION] Cleans db volume and re-runs migrations |
| `make lint` | **AVAILABLE** | Runs Ruff code analysis |
| `make format` | **AVAILABLE** | Auto-formats codebase with Ruff |
| `make backtest` | *Planned (Phase 28)* | Runs historical flood replay |
| `make evaluate` | *Planned (Phase 29)* | Computes reproducible evaluation metrics |
| `make benchmark` | *Planned (Phase 30)* | Evaluates rerouting & sync latency |
| `make demo` | *Planned (Phase 14/31)*| Launches Judge Mode scenario runner |
| `make reset` | *Planned (Phase 09)* | Resets local digital twin state |

---

## 6. Repository Architecture

```text
NEXUS/
├── apps/
│   ├── command-center/       # DEOC Command Center React application
│   └── field-app/            # Offline-First PWA for field officers
├── services/
│   ├── api/                  # Central FastAPI application & DB layer
│   ├── sync/                 # Canonical synchronization protocol & handlers
│   ├── sms/                  # SMS fallback parser & simulator
│   ├── simulation/           # Flood progression & what-if scenario engine
│   └── recommendations/      # Decision recommendations & explanation engine
├── digital_twin/             # Authoritative state manager & transition model
├── ml/                       # ML models (gradient boosting, baseline risk)
├── geospatial/               # PostGIS queries, OSM graph & routing engine
│   └── osm/
│       ├── roads/            # Parser, normalizer, distance, graph builder
│       ├── bridges/          # Bridge detection & road association
│       └── places/           # Emergency facilities & POI extraction
├── backtesting/              # Historical disaster event datasets & runner
├── data/                     # Canonical schemas, samples & provenance
│   ├── schemas/              # JSON Schemas (Draft 2020-12)
│   ├── sample/               # Synthetic deterministic fixtures
│   │   └── osm/              # Deterministic OSM synthetic graph fixture
│   ├── raw/osm/              # Raw Overpass API query artifacts (gitignored)
│   └── provenance/           # Sources, licenses & transformation registries
├── evaluation/               # Reproducible benchmark metrics & outputs
├── tests/                    # Unit, contract, and integration tests
├── scripts/
│   ├── fetch_data/           # OSM and geospatial acquisition scripts
│   └── health_check/         # Environment diagnostic scripts
├── docs/                     # Architecture, data contracts & model cards
├── demo/                     # Deterministic Judge Mode scenarios
├── security/                 # Security policy and audit logging specifications
└── infrastructure/           # Docker, compose, and database migrations
```

---

## 7. Implementation Roadmap (Phases 01–33)

- **Phase 01: Repository Initialization** *(Completed)*
- **Phase 02: Environment + Docker** *(Completed)*
- **Phase 03: PostgreSQL + PostGIS** *(Completed)*
- **Phase 04: Data Contracts + Provenance** *(Completed)*
- **Phase 05: OSM Road Graph** *(Completed)*
- **Phase 06: Geospatial Engine**
- **Phase 07: Emergency Routing**
- **Phase 08: Dynamic Rerouting**
- **Phase 09: Digital Twin**
- **Phase 10: Flood Simulation**
- **Phase 11: What-If Scenarios**
- **Phase 12: Command Center Foundation**
- **Phase 13: Live GIS Dashboard**
- **Phase 14: Judge Mode**
- **Phase 15: Incident Management**
- **Phase 16: Hospitals + Shelters**
- **Phase 17: Baseline Risk Model**
- **Phase 18: Gradient Boosting Risk Model**
- **Phase 19: Explainability + Uncertainty**
- **Phase 20: Recommendation Engine**
- **Phase 21: Human Approval + Audit**
- **Phase 22: Field PWA**
- **Phase 23: IndexedDB Offline Storage**
- **Phase 24: Service Worker**
- **Phase 25: Sync + Idempotency**
- **Phase 26: SMS Parser + Simulator**
- **Phase 27: Vulnerability Prioritization**
- **Phase 28: Historical Backtesting**
- **Phase 29: Automated Evaluation**
- **Phase 30: End-to-End Integration + Performance**
- **Phase 31: Demo + Documentation + Judge Preparation**
- **Phase 32: Security + Deployment + Final Freeze**
- **Phase 33: Mass UI/UX + Judge Experience**

---

## 8. License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.
