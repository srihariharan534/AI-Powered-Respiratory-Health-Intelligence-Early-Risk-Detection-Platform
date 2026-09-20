# NEXUS Spatial Database Infrastructure

This directory contains the database migration scripts and configuration for the spatially enabled PostgreSQL + PostGIS database.

---

## 1. Overview

NEXUS uses **PostgreSQL 16** with the **PostGIS 3.4** extension for spatial data persistence (road network graphs, flood polygons, incident markers, hospital & shelter locations).

- **Driver**: `psycopg2-binary`
- **ORM & Toolkit**: `SQLAlchemy 2.0`
- **Spatial Extensions**: `GeoAlchemy2`
- **Migration Framework**: `Alembic`

---

## 2. Running Migrations

Apply pending migrations:
```bash
make db-migrate
# or
alembic upgrade head
```

Inspect migration status:
```bash
alembic current
alembic history --verbose
```

---

## 3. Database Lifecycle Commands

- `make db-up`: Launch the PostGIS database container and wait for healthy status.
- `make db-down`: Stop the database container.
- `make db-status`: Verify database connectivity and PostGIS version.
- `make db-reset`: **Destructive action** — stops container, deletes the Docker volume `nexus-postgres-data`, and re-provisions a clean database.
