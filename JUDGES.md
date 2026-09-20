# NEXUS — Judges & Evaluators Guide

Welcome to **NEXUS (Offline-First AI Flood Response & Emergency Decision Platform)**.

This document serves as the primary walkthrough and evaluation guide for hackathon judges, technical reviewers, and operational assessors.

---

## 1. The Problem

Compound flood emergencies produce rapid operational collapse:
- **Connectivity Disappears**: Cellular networks fail, fiber cables sever, field officers work completely offline.
- **Field Reports Delayed**: Critical localized flood hazard observations cannot reach dispatch in time.
- **Infrastructure Severance**: Roads submerge, bridges collapse without warning, cutting off triage routes.
- **Triage Saturation**: Hospitals and shelters become overwhelmed without coordinated dynamic dispatching.
- **Time Pressure**: Emergency coordinators must adapt rapidly with explainable, high-integrity decision intelligence.

---

## 2. NEXUS Core Differentiator

NEXUS integrates six critical capabilities into one unified system:

```text
Offline Field Intelligence (PWA + Local IndexedDB)
+
Authoritative Emergency Digital Twin (State Single Source of Truth)
+
Dynamic Rerouting Engine (Real-time edge invalidation)
+
What-If Scenario Simulation (Deterministic infrastructure testing)
+
Explainable AI Recommendations (Uncertainty bounds & SHAP attribution)
+
Human Approval & Auditability (Mandatory human-in-the-loop sign-off)
```

---

## 3. The Hero Demonstration: "Break the System — Watch NEXUS Adapt"

The central evaluation workflow demonstrated for judges is:

```text
Flood Scenario Initialization
  → Trigger Bridge Failure
  → Dynamic Route Recalculation
  → AI Recommendation Adaptation
  → Disconnect Field App Network (Offline Mode)
  → File Field Incident (Stored Locally in IndexedDB)
  → Reconnect Network
  → Deterministic Synchronization
  → Central Digital Twin Update & Audit Trail
  → Human Coordinator Approval
```

---

## 4. Feature Implementation Status

| Feature Area | Current Status | Target Phase |
| :--- | :--- | :--- |
| Monorepo Architecture & Packaging | **IMPLEMENTED** | Phase 01 |
| Containerized Environment Foundation | **IMPLEMENTED** | Phase 02 |
| Spatially Enabled PostgreSQL 16 + PostGIS 3.4 | **IMPLEMENTED** | Phase 03 |
| SQLAlchemy 2.0 & Alembic Migrations | **IMPLEMENTED** | Phase 03 |
| Canonical Data Contracts (JSON Schema + Pydantic) | **IMPLEMENTED** | Phase 04 |
| Provenance Registries (Sources, Licenses, Transforms)| **IMPLEMENTED** | Phase 04 |
| OSM Road Graph & Geodesic Topology Engine | **IMPLEMENTED** | Phase 05 |
| Bridge Extraction & Edge Association | **IMPLEMENTED** | Phase 05 |
| Dynamic Routing & Recalculation | *PLANNED* | Phase 07–08 |
| Authoritative Digital Twin Engine | *PLANNED* | Phase 09 |
| What-If Scenario & Bridge Failure Engine | *PLANNED* | Phase 10–11 |
| Command Center GIS Dashboard | *PLANNED* | Phase 12–13 |
| Deterministic Judge Mode Controls | *PLANNED* | Phase 14 |
| Gradient Boosting Risk Model & SHAP | *PLANNED* | Phase 18–19 |
| Human-in-the-Loop Recommendation Engine | *PLANNED* | Phase 20–21 |
| Field PWA & Offline IndexedDB Storage | *PLANNED* | Phase 22–24 |
| Canonical Sync Protocol & Idempotency | *PLANNED* | Phase 25 |
| SMS Parser & Fallback Simulator | *PLANNED* | Phase 26 |
| Reproducible Evaluation & Backtesting | *PLANNED* | Phase 28–29 |
| End-to-End Polish & Mass UI/UX | *PLANNED* | Phase 31–33 |

---

## 5. Evaluation Integrity

All evaluations adhere strictly to scientific reproducibility:
- **No Fabricated Metrics**: All latency numbers, classification scores, and routing recalculation speeds are computed directly by executable benchmarks in `evaluation/results/`.
- **Transparent Provenance**: External datasets are logged in `data/provenance/`.
