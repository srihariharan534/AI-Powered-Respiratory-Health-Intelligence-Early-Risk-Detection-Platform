# NEXUS Development Environment Architecture

This document outlines the local environment, containerization design, and reproducibility strategies established in **Phase 02: Environment + Docker**.

---

## 1. System Requirements

To develop and test NEXUS locally, ensure the following core tools are installed:
- **Python**: 3.10+ (Tested on Python 3.11/3.13)
- **Node.js**: Current LTS (Node.js 20+, tracked via `.nvmrc`)
- **Package Manager**: `npm` (Version 10+) or `pnpm`
- **Docker & Docker Compose**: Docker 24+ / Docker Compose v2
- **Git**: For version control

Verify your local environment at any time using:
```bash
python scripts/health_check/check_environment.py
# or
make health-check
```

---

## 2. Python Environment Architecture

- **Dependency Authority**: Governed by standard [pyproject.toml](../../pyproject.toml) (PEP 517/518).
- **Tooling**:
  - `pytest` for unit, contract, and integration tests.
  - `ruff` for ultra-fast linting and code formatting (`ruff check .`, `ruff format .`).
- **Package Inclusion**: Monorepo packages (`digital_twin`, `ml`, `geospatial`, `backtesting`, `services`) are installed in editable development mode:
  ```bash
  pip install -e ".[dev]"
  ```

---

## 3. Frontend Workspace Architecture

The frontend components are orchestrated as an npm monorepo workspace in [package.json](../../package.json):
- `@nexus/command-center`: District Emergency Operations Center (DEOC) GIS dashboard (`apps/command-center`).
- `@nexus/field-app`: Offline-first emergency triage Progressive Web App (`apps/field-app`).

---

## 4. Docker Architecture

Containerization isolates the heterogeneous components of NEXUS into an internal bridge network:
- **Network**: `nexus-network` (bridge).
- **Service Containers**:
  - `nexus-api`: FastAPI backend container running on port `8000`.
  - `nexus-command-center`: Vite/React frontend dashboard container on port `3000`.
  - `nexus-field-app`: Progressive Web App container on port `3001`.
- **Database Service**: PostgreSQL 16 with PostGIS extension will be incorporated in **Phase 03**.

---

## 5. Environment Variables & Secret Hygiene

Configurations follow Twelve-Factor App principles:
- Copy `.env.example` to `.env` for local customizations.
- **Strict Rule**: `.env` is strictly ignored by git. Never commit live credentials, API keys, or production secrets to source control.
