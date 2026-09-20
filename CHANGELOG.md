# Changelog

All notable changes to the **NEXUS** platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

### Added - Phases 26–44 & 46: Complete Master Platform Freeze
- **Phase 26 (SMS Fallback Ingestion & Simulator)**:
  - Canonical SMS contracts conforming to `data/schemas/sms.schema.json`.
  - Deterministic regex and token parser (`services/sms/parser.py`) for compact `FLOOD <ENTITY_ID> <STATUS> <SEVERITY> <LAT> <LON>` format.
  - Ingestion gateway (`services/sms/ingestion.py`) with raw message preservation, replay protection, and Digital Twin event propagation.
  - REST endpoint `POST /api/v1/sms/ingest` and `GET /api/v1/sms/archive`.
- **Phase 27 (Vulnerability Prioritization)**:
  - Multi-factor spatial prioritization engine (`geospatial/vulnerability/prioritizer.py`) separating Exposure, Vulnerability, and Risk with explainable reasons.
  - Recommendation ranking service (`services/recommendations/vulnerability_priority/`).
- **Phase 28 & 29 (Historical Backtesting & Automated Evaluation)**:
  - Backtesting framework (`backtesting/engine.py`) with historical Chennai flood ground-truth playback (`backtesting/historical_events.py`).
  - Automated evaluation tables generated under `evaluation/results/tables/`.
- **Additional Features A–H**:
  - **Feature A (Decision Replay)**: Chronological decision timeline engine (`services/recommendations/decision_replay.py`).
  - **Feature B (Counterfactual Comparison)**: Multi-criteria operational trade-off evaluator (`services/recommendations/counterfactual.py`).
  - **Feature C (Resource Allocation Optimizer)**: Constrained emergency resource allocator prioritizing highest-risk sectors (`services/recommendations/resource_allocation/optimizer.py`).
  - **Feature D (Data Trust Layer)**: Transparent quality and freshness registry (`infrastructure/monitoring/data_trust.py`).
- **Phases 30–44 & 46 (Hardening, Security, Governance & Final System Freeze)**:
  - Complete STRIDE threat model (`security/threat-model.md`) and privacy specification (`security/privacy.md`).
  - All 176 backend unit and integration tests passing.
  - All 31 Field PWA and 28 Command Center frontend tests passing with clean production builds.
  - System entered authoritative **FINAL FREEZE**.

### Added - Phase 25: Synchronization + Idempotency + Conflict Resolution
- Canonical Synchronization Protocol (`services/sync/sync_protocol.md`):
  - Defined single source of truth for synchronization semantics, envelope formats, status codes, and failure classification.
- Authoritative Server Synchronization Engine (`services/sync/`):
  - `SyncQueueProcessor` (`services/sync/queue/processor.py`): Atomically processes batch operations with independent isolation and domain delegation.
  - `IdempotencyStore` (`services/sync/idempotency/store.py`): Thread-safe registry caching processed operations and computing deterministic SHA-256 payload hashes to detect `IDEMPOTENCY_KEY_REUSE`.
  - `ConflictResolutionEngine` (`services/sync/conflict_resolution/engine.py`): Optimistic concurrency validation checking client `base_state_version` against authoritative Digital Twin state versions, preventing silent overwrites.
  - `SyncEventLedger` (`services/sync/event_log/ledger.py`): Thread-safe append-only audit trail capturing all sync operations and lifecycle states.
  - `RetryPolicy` (`services/sync/retry/backoff.py`): Exponential backoff calculator with bounded jitter for retryable transient server errors.
- REST API Integration (`services/api/app/routes/sync.py`):
  - `POST /api/v1/sync`: Authenticated batch sync endpoint with RBAC enforcement (`FIELD_OFFICER`, `OPERATOR`, `COMMANDER`, `ADMIN`).
  - `GET /api/v1/sync/events`: Queryable audit event log.
- Client Synchronization Engine (`apps/field-app/`):
  - `ClientSyncEngine` (`src/services/sync/clientSyncEngine.ts`): Multi-tab mutual exclusion via Web Locks API (`navigator.locks`), automatic batch submission, and local IndexedDB reconciliation.
  - Connected real-time synchronization trigger and conflict badges in `SyncStatusScreen.tsx`.
- Comprehensive Verification:
  - 10 backend tests (`tests/unit/test_sync_engine.py`) validating duplicate delivery, key reuse rejection, concurrency conflicts, and audit logging.
  - 3 frontend tests (`apps/field-app/tests/syncEngine.test.ts`) validating reconciliation, conflict handling, and error recovery.
  - All 31 Field PWA tests, 28 Command Center tests, and 166 backend unit tests pass.

### Added - Phase 24: Service Worker + Offline Cache + Background Sync Foundation
- Implemented native Service Worker (`apps/field-app/public/sw.js`) with cache versioning, safe network routing, and offline navigation fallback.
- Application Shell Precaching:
  - Created segregated cache namespaces: `nexus-field-shell-v1` (core HTML/manifest/icons) and `nexus-field-assets-v1` (static scripts, styles, images).
  - Pre-caches core entry points during SW `install` event and claims clients immediately on `activate`.
- Safe Route Caching Strategies:
  - Network-First with offline fallback for HTML navigation requests.
  - Cache-First for static JS, CSS, and image assets.
  - Network-Only for dynamic API endpoints (`/api/*`), guaranteeing live data freshness and never caching mutating operations.
- Background Sync Registration & Communication:
  - Implemented `BackgroundSyncManager` with feature detection and registration for `nexus-field-outbox-sync`.
  - Service Worker broadcasts `OUTBOX_SYNC_TRIGGERED` messages to active clients upon receiving OS background sync events.
  - Client-controlled messaging protocol supporting `GET_SW_INFO` and `SKIP_WAITING`.
- Storage Isolation:
  - Service Worker cache cleanup selectively targets only caches matching `nexus-field-*`, strictly preserving Phase 23 IndexedDB stores without any data loss.
- UI & Architecture Updates:
  - Enhanced `SyncStatusScreen` with real-time Service Worker status, Background Sync support indicator, and cache versioning HUD.
  - Authored architecture documentation in `docs/architecture/service-worker.md`.
  - Added unit test suite in `tests/serviceWorker.test.ts` (9 tests passing).

### Added - Phase 23: IndexedDB Offline Storage — Durable Field Data Foundation
- Implemented native browser IndexedDB client-side persistence in `apps/field-app/src/database/` guaranteeing that field data survives browser closures, page refreshes, and device reboots without data loss.
- Centralized Database & Migration Foundation:
  - Database name: `nexus-field` (Schema Version 1) via singleton `NexusFieldDatabase` (`src/database/indexeddb/connection.ts`).
  - Migration runner (`src/database/migrations/v1.ts`) establishing 6 object stores: `incidents`, `evidence`, `assignments`, `resource_requests`, `outbox`, and `app_state`.
- Repository Abstractions & Type Separation:
  - `IncidentRepository` (`src/database/repositories/IncidentRepository.ts`): Durable incident storage, status lookups, and Phase 04 schema enforcement.
  - `EvidenceRepository` (`src/database/repositories/EvidenceRepository.ts`): Metadata association and indexing by incident ID.
  - `AssignmentRepository` (`src/database/repositories/AssignmentRepository.ts`): Local mission caching with distinct `is_cached` flags.
  - `ResourceRequestRepository` (`src/database/repositories/ResourceRequestRepository.ts`): Local asset requisition persistence.
  - `OutboxRepository` (`src/database/repositories/OutboxRepository.ts`): Durable queue of operations awaiting future Phase 25 synchronization with collision-resistant operation IDs (`OP-<timestamp>-<hash>`).
  - `AppStateRepository` (`src/database/repositories/AppStateRepository.ts`): Key-value store for client runtime settings.
- Atomic Offline Create Workflow (`TransactionCoordinator`):
  - Executes multi-store `readwrite` IndexedDB transactions committing `incident`, `evidence`, and `outbox` records atomically.
  - Full rollback and honest user-facing storage error messages when storage is constrained.
- UI & Service Integration:
  - Updated `IncidentReportScreen`, `ResourceRequestScreen`, and `EvidenceCaptureScreen` to display explicit "SAVED ON DEVICE — PENDING SYNC" feedback and prevent duplicate submissions.
  - Connected `SyncStatusScreen` and `OfflineIndicator` to display real category counts directly from IndexedDB outbox records.
  - Hydrated `FieldAppContext` and `SyncQueueService` from durable storage on application launch.
- Rigorous Verification & Tests:
  - Added 10 unit and transaction tests (`tests/indexeddb.test.ts`) validating schema creation, coordinate boundary validation, atomic creation, and restart recovery.
  - All 19 Field PWA tests, 28 Command Center tests, and 156 backend unit tests pass.
  - Authored offline storage architecture documentation (`docs/architecture/offline-storage.md`).

### Added - Phase 22: Field PWA — Offline-First Field Officer Application Foundation
- Implemented `apps/field-app`, a touch-first, mobile-responsive Progressive Web App (PWA) tailored for field officers, search & rescue teams, and emergency personnel operating in severed or degraded network environments.
- Mobile-First Tactical UX & Design System:
  - Enforced minimum 48px touch targets compliant with responder glove operation.
  - Tactical high-contrast dark theme (`#0b1329` / `#0f172a` slate base with vivid status highlights).
  - Sticky bottom navigation bar optimized for single-handed thumb operation (`Home`, `Report`, `Map`, `Sync`).
- Bilingual Localization (EN / தமிழ்):
  - Created complete English and Tamil UI translation dictionaries (`src/i18n/en.json`, `src/i18n/ta.json`).
  - Dynamic locale switcher persisted in context with instant zero-refresh toggling.
- Canonical Field Incident Reporting (`src/screens/incident-report/`):
  - Strictly aligned with Phase 04 `incident.schema.json` data contracts.
  - Multi-category event tagging (`FLOOD_INUNDATION`, `ROAD_BLOCKED`, `BRIDGE_FAILURE`, `EMBANKMENT_BREACH`, etc.).
  - WGS84 coordinates capture with GPS accuracy radius and manual coordinate fallback input.
- Tactical Operations & Evidence Management:
  - **Tactical Assignment HUD** (`src/screens/assignment/`): Mission card displaying priorities, target coordinates, and interactive status progression (`ASSIGNED -> EN_ROUTE -> ON_SCENE -> COMPLETED`).
  - **Evidence Capture** (`src/screens/evidence-capture/`): Media capture simulation attaching GPS coordinates, ISO timestamps, and descriptions to synchronization queue.
  - **Resource Requests** (`src/screens/resource-request/`): Tactical asset requisition form for rescue boats, medical kits, rations, and pumps.
  - **Cached Map Foundation** (`src/screens/cached-map/`): Vector tile foundation surface showing mission waypoints, coordinate HUD, and explicit offline availability disclaimers.
- Zero-Data Structured SMS Fallback (`src/screens/sms-fallback/`):
  - Formats emergency broadcast into deterministic Phase 04 SMS string (`FLOOD <ENTITY_ID> <STATUS> <SEVERITY> <LAT> <LON>`) within the 160-character cellular limit.
  - One-tap clipboard copy and native `sms:?body=` URI launcher.
- Offline Synchronization Queue & Connectivity HUD (`src/services/`):
  - In-memory `SyncQueueService` and `ConnectivityService` with listener pub/sub.
  - Real-time connectivity simulation bar allowing officers to simulate `ONLINE` and `OFFLINE` modes.
  - Synchronizer monitor displaying pending action counts, status indicators, and manual retry triggers.
- Unit Testing & Phase Boundary Adherence:
  - Added 9 Vitest integration tests (`tests/fieldApp.test.tsx`) covering navigation, GPS capture, fallback, SMS encoding, and queuing.
  - Added lightweight placeholders for Service Worker (`cache-strategy.ts`, `offline-sync.ts`, `background-sync.ts`) and IndexedDB (`database/indexeddb/index.ts`) in strict respect of Phase 23/24/25 boundaries.
  - Produced architectural guides (`docs/architecture/field-pwa.md`, `docs/ux/field-workflow.md`, `apps/field-app/README.md`).

### Added - Phase 21: Human Approval + Audit
- Implemented complete human governance and audit layer around NEXUS recommendations adhering to the core principle: *NEXUS recommends, an authorized human decides, the system records what happened.*
- Created centralized `RecommendationStateMachine` (`services/recommendations/governance/state_machine.py`) enforcing valid lifecycle transitions (`PENDING -> APPROVED / REJECTED / EXPIRED`) and rejecting illegal backward/lateral transitions with structured errors.
- Established server-enforced Role-Based Access Control (`services/recommendations/governance/roles.py`):
  - Defined roles: `VIEWER`, `FIELD_OFFICER`, `OPERATOR`, `APPROVER`, `COMMANDER`, `ADMIN`.
  - Backend authorization dependency extracting and verifying `X-Actor-Id` and `X-Actor-Role` headers.
- Implemented state freshness and operational precondition validation:
  - Validates `source_state_version == current_state_version`; stale proposals are invalidated as `EXPIRED` and approvals rejected with `HTTP 409 Conflict` (`RECOMMENDATION_STALE`).
  - Precondition checks verify target incidents remain active (rejecting if `RESOLVED`/`CANCELLED`) and facilities remain operational with available capacity (rejecting if `CLOSED` or full).
  - Mode isolation ensures `SIMULATION` and `DEMO` recommendations cannot be approved into live operations.
- Built thread-safe append-only `AuditLedger` (`services/recommendations/governance/audit_ledger.py`):
  - Immutably records structured audit events: `RECOMMENDATION_CREATED`, `RECOMMENDATION_VIEWED`, `RECOMMENDATION_APPROVED`, `RECOMMENDATION_REJECTED`, `RECOMMENDATION_EXPIRED`, `APPROVAL_BLOCKED`.
  - Saves durable `RecommendationDecisionRecord` preserving complete historical context with idempotency token support.
- Upgraded REST API (`services/api/app/routes/recommendations.py`):
  - Secured `POST /approve`, `POST /reject`, `POST /expire`, `POST /generate`, and `GET /audit/ledger` endpoints with RBAC dependencies.
- Enhanced Command Center UI (`apps/command-center/src/pages/OperationalPages.tsx`):
  - **Recommendations Page**: Role switcher, stale state warning alerts (`⚠ RECOMMENDATION STALE`), confirmation dialogs for consequential actions, and mandatory rejection reason inputs.
  - **Audit Page**: Chronological governance timeline displaying event badges, timestamps, actor roles, and decision reasons.
- Documented governance specifications:
  - Created architecture guide (`docs/architecture/human-approval-audit.md`).
  - Created security specifications (`security/authorization.md`, `security/audit-log.md`).
  - Updated `docs/ai/failure-modes.md` and `docs/ai/limitations.md`.
- Added 10 unit and governance tests (`tests/unit/test_human_approval_audit.py`) validating state transitions, RBAC enforcement, stale state protection, concurrency safety, idempotency, and API endpoints. All 156 unit tests and 28 frontend tests pass.

### Added - Phase 20: Operational Recommendation Engine
- Implemented dedicated recommendations subsystem (`services/recommendations/`) delivering deterministic, offline-capable operational guidance across incident priority, medical triage, shelter intake, and corridor routing.
- Established canonical schemas and contracts (`services/recommendations/contracts.py`):
  - Strict compliance with `data/schemas/recommendation.schema.json`.
  - Enforced `requires_human_approval: true` across every recommendation to guarantee human-in-the-loop operational sovereignty. Zero autonomous emergency actions.
  - Linked all recommendations to immutable `source_state_version`. Stale recommendations are invalidated (`EXPIRED`) upon digital twin state progression, with approval rejected via `HTTP 409 Conflict`.
- Implemented domain engines:
  - `IncidentPriorityEngine` (`services/recommendations/incident_priority/`): Multi-factor incident triage synthesizing risk model probability, reported severity, geospatial water depth exposure, and corridor accessibility.
  - `HospitalSelectionEngine` (`services/recommendations/hospital_selection/`): Medical receiving facility selection enforcing hard operational constraints (excluding full or evacuating hospitals) and scoring based on travel distance and available bed capacity.
  - `ShelterSelectionEngine` (`services/recommendations/shelter_selection/`): Evacuation shelter allocation filtering out closed/full camps and ranking by capacity and generator/water utility resilience.
  - `RouteRecommendationEngine` (`services/recommendations/evacuation/`): Safe corridor routing integrating Phase 07/08 routing engines to bypass flooded segments.
- Built multi-factor scoring and ranking system (`services/recommendations/scoring/`):
  - Transparent normalized scoring with policy versioning (`policy-v1.0`).
  - Empirical uncertainty bounding derived from facility volatility and travel time variance without fabricating false confidence.
- Built stateful service layer (`services/recommendations/service.py`) with append-only audit ledger (`RecommendationAuditEntry`).
- Implemented REST API (`services/api/app/routes/recommendations.py`):
  - `GET /api/v1/recommendations`: List recommendations filtered by status or action.
  - `GET /api/v1/recommendations/{id}`: Single recommendation retrieval.
  - `POST /api/v1/recommendations/generate`: Dynamic recommendation generation.
  - `POST /api/v1/recommendations/{id}/approve`: Operator authorization with state freshness verification.
  - `POST /api/v1/recommendations/{id}/reject`: Operator rejection with recorded rationale.
  - `GET /api/v1/recommendations/audit/ledger`: Historical decision audit query.
- Enhanced Command Center UI (`apps/command-center/src/pages/OperationalPages.tsx`):
  - Full-featured **Recommendations** page with domain and status filtering, factor weight breakdowns, and interactive Authorize / Reject dialogs.
- Created architecture guide (`docs/architecture/recommendation-engine.md`) and updated Responsible AI guidelines (`docs/ai/responsible-ai.md`).
- Added 8 unit and integration tests (`tests/unit/test_recommendation_engine.py`) covering scoring normalization, hard constraint exclusion, engine recommendations, state version conflict handling, rejection audit ledgers, and API endpoints. All 146 unit tests and 28 frontend tests pass.

### Added - Phase 19: Explainability + Uncertainty
- Implemented dedicated explainability package (`ml/explainability/`) providing feature attributions, probability calibration, uncertainty diagnostics, and counterfactual sensitivity analysis.
- Implemented canonical explainability contracts (`ml/explainability/contracts.py`):
  - `LocalExplanation`, `GlobalExplanation`, `CalibrationResult`, `UncertaintyReport`, `CounterfactualSensitivity`, and `ComprehensiveRiskExplanation`.
- Built feature attribution engines (`ml/explainability/feature_attribution/`):
  - `LogisticRegressionExplainer`: Computes exact log-odds local feature attributions ($w_j \cdot z_j$) and verifies mathematical additive reconstruction ($\text{logit}(p) = w_0 + \sum w_j z_j$) with error $< 10^{-5}$.
  - `GradientBoostingExplainer`: Decomposes tree leaf routing into probability margins and extracts authoritative population Gini impurity rankings.
- Built reusable probability calibration layer (`ml/explainability/confidence/calibration.py`):
  - Supports Platt scaling (sigmoid) and isotonic regression fitted strictly on validation split ($N=45$) with zero test data leakage.
  - Transparently reports validation Brier scores and expected calibration error (ECE).
- Built multi-dimensional uncertainty & data quality diagnostics (`ml/explainability/uncertainty/`):
  - Distinguishes data completeness and missing feature imputation from model distribution shift.
  - Computes standardized centroid Euclidean distance ($D = \sqrt{\sum z_j^2}$) classifying inputs into `IN_DISTRIBUTION` ($D \le 3.2$), `WARNING` ($3.2 < D \le 4.8$), and `OUT_OF_DISTRIBUTION` ($D > 4.8$).
- Built bounded counterfactual sensitivity engine (`ml/explainability/counterfactual/sensitivity.py`):
  - Conducts deterministic parameter sensitivity search enforcing strict physical domain bounds (non-negative rainfall, non-negative river distance, elevation $\ge -50\text{m}$, rainfall $1\text{h} \le 24\text{h}$).
  - Strictly non-causal: reports hypothetical model parameter sensitivities without claiming physical civil defense intervention.
- Extended REST API (`services/api/app/routes/risk.py`) with `POST /api/v1/risk/explain` endpoint returning authoritative predictions, local attributions, calibration reports, uncertainty diagnostics, and counterfactual sensitivities.
- Added evaluation script (`scripts/evaluate/evaluate_explainability.py`) generating `feature_importance.csv`, `calibration_metrics.csv`, and `counterfactual_examples.csv`.
- Added documentation:
  - Created architecture guide (`docs/ai/explainability.md`).
  - Updated Model Card (`docs/ai/model-card.md`), Responsible AI (`docs/ai/responsible-ai.md`), and Failure Modes (`docs/ai/failure-modes.md`).
- Added 11 unit and integration tests in `tests/unit/test_explainability.py` covering additive reconstruction, calibration, uncertainty diagnostics, counterfactual boundaries, and API endpoints. All 138 unit tests pass.

### Added - Phase 18: Gradient Boosting Risk Model
- Implemented non-linear `GradientBoostingRiskModel` under `ml/risk_model/gradient_boosting/model.py` wrapping standard library `sklearn.ensemble.GradientBoostingClassifier`.
- Zero external bloat: implemented using existing scikit-learn without introducing heavy dependencies (`xgboost`, `lightgbm`, or `catboost`).
- Enforced identical feature contracts (`RiskFeatureRecord`), identical binary target (`operational_flood_risk`), and identical fixed holdout partition ($N=75$, 25% stratified test split) to guarantee scientifically rigorous comparison with Phase 17.
- Added SHA-256 dataset provenance fingerprinting (`compute_dataset_fingerprint`) across raw feature data to ensure bit-level reproducibility.
- Implemented Gini feature importance extraction and tree-leaf local attributions for single and batch predictions.
- Created deterministic training CLI script (`scripts/train/train_gradient_boosting.py`) serializing model artifact `gradient_boosting_v1.joblib` and comprehensive `gradient_boosting_v1_metadata.json`.
- Created comparative model evaluation CLI script (`scripts/evaluate/evaluate_risk_models.py`) running side-by-side performance benchmarks (Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, Brier score, ECE calibration error, and inference latency).
- Conducted empirical evidence-based model evaluation:
  - Phase 17 Logistic Regression baseline demonstrated superior overall performance (94.67% accuracy, 76.47% recall, 0.9888 ROC-AUC, 0.0412 Brier score) over Phase 18 Gradient Boosting (89.33% accuracy, 52.94% recall, 0.9594 ROC-AUC, 0.0772 Brier score).
  - Maintained Logistic Regression as default production model while exposing Gradient Boosting as an alternative non-linear option.
- Updated REST API (`services/api/app/routes/risk.py`) supporting dynamic multi-model routing via `model_version` query parameter and payload field across `/predict`, `/batch`, `/model-info`, and `/geojson`.
- Updated documentation:
  - Model Card (`docs/ai/model-card.md`) updated with dual-model specifications and comparative analysis.
  - Evaluation report (`docs/ai/evaluation.md`) documenting comparative test results and calibration curves.
  - Risk Model architecture guide (`docs/architecture/risk-model.md`) explaining model pipeline design.
  - Provenance registry (`data/provenance/transformations.yaml`) recording training and evaluation runs.
- Added 9 unit tests in `tests/unit/test_gradient_boosting_model.py` covering model initialization, deterministic training, feature importance summation, inference contracts, fingerprinting, joblib serialization roundtrip, and API multi-model routing. All 127 unit tests pass.

### Added - Phase 17: Baseline Flood Risk Model
- Built transparent and reproducible machine-learning risk modeling package under `ml/risk_model/`.
- Implemented canonical tabular contracts (`ml/risk_model/contracts.py`) with Pydantic validation:
  - `RiskFeatureRecord` enforcing physical parameter bounds (non-negative rainfall, rainfall 1h $\le$ 24h consistency, and coordinate validity).
  - Out-of-distribution input rejection returning explicit validation errors without silent clamping.
  - `RiskPredictionOutput` returning estimated probability, predicted binary class, feature version, timestamp, and local linear feature contributions.
- Created deterministic feature preprocessing pipeline (`ml/risk_model/preprocessing.py`) fitting median imputations and standard scalers strictly on training splits.
- Implemented interpretable L2-regularized logistic regression baseline (`ml/risk_model/baseline/logistic_regression/model.py`) providing standardized coefficient extraction, sign direction, and local attributions ($\beta_j \cdot z_j$).
- Built evaluation suite (`ml/risk_model/baseline/logistic_regression/evaluation.py`) computing accuracy, precision, recall, F1, ROC-AUC, PR-AUC, Brier score, and calibration reliability analysis.
- Proven statistically superior performance over naive majority-class baseline (ROC-AUC: 0.9888 vs 0.5000; Brier Score: 0.0412 vs 0.1753).
- Created deterministic training and standalone evaluation CLI commands (`scripts/train/train_baseline_risk.py` and `scripts/evaluate/evaluate_baseline_risk.py`).
- Exported reproducible benchmark tables to `evaluation/results/tables/model_comparison.csv` and `headline_metrics.csv`.
- Built REST API endpoints (`services/api/app/routes/risk.py`) for `/api/v1/risk/predict`, `/batch`, `/model-info`, and `/geojson` (EPSG:4326 FeatureCollection export).
- Replaced placeholder Vulnerability view with an active Command Center analysis dashboard (`apps/command-center/src/pages/VulnerabilityPage.tsx`) featuring real-time risk roster, KPI summary metrics, interactive feature predictor sandbox, and prominent non-autonomous advisory warnings.
- Added comprehensive AI governance and safety documentation:
  - Model Card (`docs/ai/model-card.md`)
  - Responsible AI specification (`docs/ai/responsible-ai.md`)
  - Limitations analysis (`docs/ai/limitations.md`)
  - Failure modes catalog (`docs/ai/failure-modes.md`)
  - Data Card update (`docs/data/data-card.md`)
  - Provenance registries (`data/provenance/sources.yaml`, `licenses.yaml`, `transformations.yaml`)
- Added 13 unit and integration tests (`tests/unit/test_baseline_risk_model.py`) and 3 frontend tests (`apps/command-center/src/pages/__tests__/vulnerability-page.test.tsx`), maintaining 100% test pass rates across Python (118/118) and TypeScript (28/28).
- Implemented `FacilityStatusChangedEvent` in Digital Twin state engine (`digital_twin/events/facility_status_changed.py`) supporting authoritative operational status changes (`ACTIVE`, `LIMITED_OPERATIONS`, `EVACUATING`, `CLOSED`) with immutable provenance and actor auditing.
- Extended Digital Twin transitions (`digital_twin/state/transitions.py`) and state manager (`digital_twin/state/state_manager.py`) with transition validation and duplicate/no-op rejection.
- Created PostGIS relational persistence models (`services/api/app/models/facility.py`) with `HospitalModel` and `ShelterModel` storing EPSG:4326 point geometries, capacity telemetry, backup power, water supply, and contact info.
- Implemented authoritative `FacilityService` (`services/api/app/repositories/facility_service.py`):
  - Enforced mathematical bounds ($0 \le \text{available\_capacity} \le \text{capacity}$).
  - Integrated with Digital Twin state manager emitting `CapacityUpdatedEvent` and `FacilityStatusChangedEvent`.
  - Built optimistic concurrency control rejecting stale mutations via `FacilityStateVersionConflictError` (`HTTP 409 Conflict`).
  - Added spatial flood exposure evaluation using Phase 10 exposure logic, strictly upholding the `EXPOSED != CLOSED` operational rule.
  - Implemented immutable audit logging per facility.
- Built REST API endpoints for hospitals (`/api/v1/hospitals`) and shelters (`/api/v1/shelters`) with deterministic filtering (`status`, `accessibility`, `has_available_capacity`, `emergency_available`), sorting, pagination, and capacity/status updates.
- Extended Phase 11 What-If Scenario Engine with `ShelterCapacityModification` and `shelter_capacity` scenario type for isolated counterfactual simulations.
- Updated Command Center GIS map markers and detail panel with rich canonical facility attributes and flood exposure visual banners.
- Created dedicated Command Center operational management pages (`apps/command-center/src/pages/HospitalsPage.tsx` and `SheltersPage.tsx`) featuring real-time roster tables, KPI stat cards, capacity adjustment dialogs, status transition controls, and Leaflet mini-maps.
- Added comprehensive unit and integration tests (17 Python unit tests in `tests/unit/test_facility_management.py`, 5 React testing library tests in `apps/command-center/src/pages/__tests__/facilities-pages.test.tsx`), maintaining 100% passing test suites across both environments.
- Added comprehensive architecture and domain documentation in `docs/architecture/facility-management.md`.
- Implemented canonical incident lifecycle state machine (`services/api/app/schemas/incident_lifecycle.py`) enforcing valid state transitions (`OPEN` → `ACKNOWLEDGED` → `IN_PROGRESS` → `RESOLVED` / `CANCELLED`).
- Enforced strict lifecycle transitions within Digital Twin state transitions (`digital_twin/state/transitions.py`), rejecting illegal status updates.
- Built relational and PostGIS spatial model (`services/api/app/models/incident.py`) with EPSG:4326 geometry point mapping.
- Implemented authoritative `IncidentService` (`services/api/app/repositories/incident_service.py`) supporting:
  - Incident registration with GeoJSON validation and initial state version assignment.
  - Digital Twin integration via `IncidentCreatedEvent` and `IncidentStatusChangedEvent`.
  - Optimistic concurrency control via `expected_state_version` checks, rejecting stale writes with `HTTP 409 Conflict`.
  - Append-only audit logging recording `actor`, `action`, `previous_state`, `new_state`, and operational notes.
  - Filtering by status, severity, event category, and source with deterministic pagination.
- Built incident REST API endpoints (`services/api/app/routes/incidents.py`).
- Upgraded Command Center incident interface (`apps/command-center/src/pages/IncidentsPage.tsx`) with dispatch roster table, filter bar, contextual detail inspector, validated action buttons, registration form, and audit timeline.
- Added 10 backend unit tests (`tests/unit/test_incident_management.py`) and 2 frontend unit tests (`apps/command-center/src/pages/__tests__/incidents-page.test.tsx`).

### Added - Phase 14: Judge Mode — Competition Demonstration Experience
- Built dedicated, presentation-ready **Judge Mode** (`/judge-mode` in `apps/command-center/src/pages/JudgeModePage.tsx`).
- Created deterministic scenario manifest (`demo/judge-mode/judge-scenario.json`) defining the 8-step hero demonstration:
  1. Baseline Operational State
  2. Flood Inundation Scenario (+1.0m)
  3. Structural Bridge Failure Cascade (Bridge B-001 → Road R-101)
  4. Phase 08 Dynamic Rerouting Triggered (+1.4 km, +2.7 min detour via Northern Flyover)
  5. Field Connectivity Loss (Offline Mode)
  6. Offline Field Incident Capture (Local storage without data loss)
  7. Network Restored & Deterministic Synchronization (Twin bumped to v44)
  8. Phase 11 What-If Counterfactual Sandbox (Hospital capacity reduction without live state mutation)
- Implemented `JudgeModeManager` state machine supporting sequential progression (<kbd>→</kbd>), rollback (<kbd>←</kbd>), and safe reset (<kbd>R</kbd>).
- Integrated fullscreen presentation mode and causal chain synthesizer component.
- Added comprehensive unit tests (`apps/command-center/src/pages/__tests__/judge-mode.test.tsx`) verifying deterministic transitions and reset safety.
- Created Judge demonstration documentation (`docs/demo/judge-mode.md`) and technical defense guide (`docs/demo/judge-qa.md`).

### Added - Phase 13: Live GIS Command Center Dashboard
- Transformed Command Center foundation into a live GIS command surface (`apps/command-center/src/components/command-map/`).
- Integrated Leaflet map with CartoDB Dark Matter tiles, preserving standard GeoJSON `WGS84 [longitude, latitude]` convention.
- Implemented core operational GIS layers:
  - **Flood Layer**: Visualizes Phase 10 simulated inundation polygons with severity color coding, depth indicators, and explicit simulation styling.
  - **Road Layer**: Displays baseline OSM road geometries combined with dynamic operational states (Open, Restricted, Blocked).
  - **Bridge Layer**: Maps bridge entities and structural failure propagation from Digital Twin state.
  - **Incident Layer**: Visualizes triaged emergency incident markers with severity-coded icons.
  - **Facility Layer**: Maps hospitals (✚) and shelters (⛺) with live bed capacity and power backup telemetry.
  - **Dynamic Route Layer**: Visualizes active route detours alongside invalidated corridors with distance and delay deltas.
- Implemented accessible `MapControls` for layer toggling and view centering.
- Implemented accessible `MapLegend` with non-color symbols and textual labels.
- Implemented `DetailPanel` for inspecting rich attributes across flood zones, roads, bridges, incidents, facilities, and rerouted corridors.
- Implemented counterfactual scenario toggling (`BASELINE` vs `FLOOD SCENARIO`) with prominent visual indicators preventing confusion between real and simulated data.
- Added comprehensive frontend unit tests (16 tests passing) and architecture documentation in `docs/architecture/live-gis-dashboard.md`.

### Added - Phase 12: Command Center Foundation
- Built foundational frontend application shell for NEXUS Command Center (`apps/command-center`).
- Implemented core routing hierarchy via React Router DOM across all 10 planned operational routes: `/dashboard`, `/incidents`, `/simulation`, `/digital-twin`, `/hospitals`, `/shelters`, `/vulnerability`, `/recommendations`, `/audit`, and `/judge-mode` (with fallback 404 page).
- Implemented global state management via `AppContext` managing connection status (`ONLINE`, `DEGRADED`, `OFFLINE`), data mode (`REAL`, `SIMULATION`, `DEMO`), Digital Twin state version authority, and user role session.
- Implemented reusable operational UI primitives (`apps/command-center/src/components/ui/`) including `StatusIndicator`, `SeverityBadge`, `DataModeBadge`, `DigitalTwinBadge`, `Card`, `Button`, and feedback states (`LoadingState`, `EmptyState`, `ErrorState`).
- Established centralized API client (`apps/command-center/src/services/api-client.ts`) with timeout handling, cancellation, and structured `ApiError` mapping.
- Added comprehensive frontend unit tests (11 passing tests across UI primitives, navigation layouts, and API error scenarios) using Vitest and `@testing-library/react`.
- Maintained strict Phase 12 boundaries: no full GIS map rendering (Phase 13 reserved), no Judge Mode execution (Phase 14 reserved), no recommendation scoring logic (Phase 20 reserved), and zero fabricated live telemetry data.

### Added - Phase 11: What-If Scenario Engine
- Implemented isolated scenario engine (`services/simulation/`) enabling safe counterfactual simulation without mutating live Digital Twin state.
- Implemented formal What-If scenario models (`services/simulation/models.py`) supporting `flood_level`, `bridge_failure`, `hospital_capacity`, `resource_shortage`, and multi-modification `compound` scenarios.
- Added strict state version validation (`services/simulation/validator.py`) rejecting version mismatches and invalid entity references.
- Implemented isolated copy-on-write state forking (`DigitalTwinStateManager.fork()` and `StateOverlay.clone()`).
- Reused Phase 10 Flood Simulation Engine to model scenario inundation and exposure in isolated state.
- Reused Phase 08 Dynamic Rerouting to evaluate route invalidation and calculate diversion paths.
- Built counterfactual impact analysis and deterministic causal chain synthesizer (`services/simulation/impact.py`).
- Added 7 comprehensive unit and integration tests (`tests/unit/test_what_if_scenarios.py`) and architecture documentation in `docs/architecture/what-if-scenarios.md`.

### Added - Phase 10: Flood Simulation Engine
- Implemented formal scenario models (`geospatial/flood/scenario.py`) supporting `WATER_LEVEL`, `DEPTH_INCREMENT`, and `EXPLICIT_POLYGON` modes with explicit simulation metadata (`mode="SIMULATION"`).
- Implemented configurable severity classification (`geospatial/flood/thresholds.py`) mapping water depths to `LOW`, `MODERATE`, `SEVERE`, and `EXTREME` categories with non-negative depth guarantees.
- Implemented deterministic flood extent representation (`geospatial/flood/extent.py`) with metric area calculation and empty-geometry handling.
- Implemented elevation-based inundation model (`geospatial/flood/model.py`) calculating water depth surfaces over grid terrain without claiming full hydrodynamic modeling.
- Built reusable spatial exposure engine (`geospatial/flood/exposure.py`) for roads, bridges, hospitals, shelters, and incidents with configurable road closure thresholds.
- Implemented comparative scenario analysis (`geospatial/flood/comparison.py`) calculating newly flooded land areas and newly affected infrastructure.
- Added GeoJSON Feature and FeatureCollection serialization (`geospatial/flood/serialization.py`).
- Integrated with Phase 09 Digital Twin (`FloodUpdatedEvent`, `RoadStatusChangedEvent`) and Phase 08 Dynamic Routing (`StateOverlay`).
- Added 16 unit and integration tests (`tests/unit/test_flood_simulation.py`) and architecture documentation in `docs/architecture/flood-simulation.md`.

### Added - Phase 09: Digital Twin — Emergency Operational State Authority
- Implemented core Digital Twin state authority (`digital_twin/state/state_manager.py`) maintaining versioned operational state across emergency entities.
- Implemented typed operational entity models (`digital_twin/entities/`) for `roads`, `bridges`, `hospitals`, `shelters`, `rescue_teams`, `incidents`, `flood_zones`, `population`, and `vulnerable_groups`.
- Implemented immutable domain events (`digital_twin/events/`) with stable event IDs, UTC timestamps, and provenance sources (`FIELD_REPORT`, `COMMAND_CENTER`, `SIMULATION`, `SYSTEM`, `IMPORT`, `TEST_FIXTURE`).
- Implemented pure deterministic state transitions (`digital_twin/state/transitions.py`) with strict validation (capacity bounds, status validation, no-op detection).
- Implemented idempotent event application preventing duplicate updates or version bumps on re-submitted events.
- Implemented point-in-time snapshots (`TwinSnapshot`) and deterministic sequential event replay (`DigitalTwinStateManager.replay`).
- Implemented bridge-to-road causal propagation preserving causal links (`caused_by_event_id`) in the append-only in-memory audit log.
- Implemented zero-conflict synchronization with Phase 08's `StateOverlay`, directly triggering dynamic route invalidation and recalculation via `DynamicRerouter`.
- Added 12 comprehensive unit and integration tests (`tests/unit/test_digital_twin.py`) and architecture documentation in `docs/architecture/digital-twin.md`.

### Added - Phase 08: Dynamic Rerouting Engine
- Implemented non-destructive operational road state overlay (`geospatial/routing/state_overlay.py`, `dynamic_state.py`) providing precedence over the immutable base OSM graph.
- Implemented bridge-to-road state propagation mapping bridge operational closures to associated road segments and graph edges.
- Added route validation (`is_route_valid`) detecting blocked or restricted road edges along existing routes.
- Built conditional dynamic rerouter (`geospatial/routing/rerouting.py`) triggering recalculations with Phase 07 `EmergencyRouter` only when routes are invalidated.
- Implemented structured route comparison (`geospatial/routing/route_comparison.py`) calculating metric deltas (distance, duration) and edge set differences.
- Implemented deterministic machine-readable route explanations (`ReroutingExplanation`) explaining reroute rationale without LLM hallucination.
- Added structured failure handling for severed networks (`NO_PATH_AFTER_STATE_CHANGE`).
- Supported state versioning and non-destructive rollback restoring baseline OSM conditions.
- Added 8 unit tests in `tests/geospatial/test_dynamic_rerouting.py` and architectural reference in `docs/architecture/dynamic-rerouting.md`.

### Added - Phase 07: Emergency Routing Engine
- Built the foundational emergency routing engine (`geospatial/routing/`) on top of the Phase 05 OSM road graph and Phase 06 geospatial engine.
- Implemented `RoutingGraphAdapter` wrapping NetworkX `MultiDiGraph` and `RoadGraphDefinition` to isolate routing algorithms from low-level graph internals.
- Added geodesic nearest road node snapping (`geospatial/routing/nearest_node.py`) using Phase 06 Haversine calculations.
- Implemented `EmergencyRoutingPolicy` and constraint evaluation (`geospatial/routing/constraints.py`) respecting road directionality, road status (`OPEN`, `RESTRICTED`, `BLOCKED`, `UNKNOWN`), accessibility rules, and vehicle clearance.
- Implemented dual-mode cost calculation (`geospatial/routing/costs.py`) supporting distance minimization and travel-time minimization with documented speed fallbacks.
- Implemented shortest-path solvers (`geospatial/routing/router.py`) providing deterministic Dijkstra and admissible A* search algorithms.
- Implemented route path reconstruction and GeoJSON serialization (`geospatial/routing/route.py`, `serialization.py`).
- Added 9 unit tests in `tests/geospatial/test_routing.py` and architectural reference in `docs/architecture/emergency-routing.md`.

### Added - Phase 06: Geospatial Engine & Spatial Analysis Foundation
- Implemented core reusable spatial analysis package (`geospatial/spatial_analysis/`) providing coordinate validation, UTM projection, metric buffering, distance, clipping, containment, proximity, and GeoJSON conversion.
- Built strict coordinate & geometry validation (`geospatial/spatial_analysis/validation.py`) rejecting out-of-bounds, infinite, or topologically self-intersecting geometries.
- Added dynamic UTM zone lookup and bidirectional WGS84/UTM reprojections (`geospatial/spatial_analysis/transform.py`).
- Implemented Haversine geodesic distance, line length, and polygon area calculations (`geospatial/spatial_analysis/distance.py`).
- Implemented true metric buffering via local UTM planar transformations (`geospatial/spatial_analysis/buffer.py`).
- Built spatial predicates including `intersects`, `intersection_geometry`, `batch_intersects`, `contains`, `within`, and `covers` (`geospatial/spatial_analysis/predicates.py`).
- Implemented proximity queries and nearest-feature searches with deterministic tie-breaking (`geospatial/spatial_analysis/proximity.py`).
- Added bidirectional GeoJSON geometry and FeatureCollection serialization (`geospatial/spatial_analysis/geojson.py`).
- Integrated OSM road graph geometries with the spatial engine for length, proximity, and flood intersection calculations (`tests/geospatial/test_osm_integration.py`).
- Prepared domain foundation contracts (`geospatial/elevation`, `geospatial/rainfall`, `geospatial/flood`, `geospatial/population`, `geospatial/vulnerability`) without fabricated telemetry.
- Documented complete architecture in `docs/architecture/geospatial-engine.md`.
- Added 35 targeted unit tests in `tests/geospatial/` and verified PostGIS spatial operators in `tests/integration/test_postgis.py`.

### Added - Phase 05: OSM Road Graph
- Created OpenStreetMap live data acquisition script (`scripts/fetch_data/fetch_osm.py`) supporting configurable bounding boxes, place tags, and dry-run output via Overpass QL.
- Implemented OpenStreetMap parsing, highway classification, and normalization modules (`geospatial/osm/roads/parser.py`, `normalizer.py`, `models.py`).
- Implemented geodesic distance calculations using the Haversine formula (`geospatial/osm/roads/distance.py`) calculating cumulative meters along road segments.
- Built directed road graph topology builder (`geospatial/osm/roads/graph_builder.py`) supporting one-way constraints, bidirectional links, and emitting both NetworkX `MultiDiGraph` and serializable `RoadGraphDefinition`.
- Implemented bridge detection and road relationship modeling (`geospatial/osm/bridges/models.py`).
- Implemented emergency places/facilities extraction foundation (`geospatial/osm/places/__init__.py`).
- Created deterministic synthetic OSM test fixture (`data/sample/osm/synthetic_osm_fixture.json`).
- Added unit tests: `test_osm_parser.py`, `test_road_normalization.py`, `test_bridge_parser.py`, `test_graph_builder.py`, `test_coordinate_convention.py`.
- Updated provenance registries (`sources.yaml`, `transformations.yaml`), data quality guidelines (`docs/data/data-quality.md`), and created `docs/data/osm.md`.

### Added - Phase 04: Data Contracts + Provenance
- Established canonical JSON Schemas under `data/schemas/` for `incident`, `road`, `hospital`, `shelter`, `recommendation`, and `sms`.
- Implemented aligned Pydantic v2 data contract models under `services/api/app/schemas/`.
- Created deterministic synthetic fixtures under `data/sample/`.
- Established authoritative provenance registries under `data/provenance/`.

### Added - Phase 03: PostgreSQL + PostGIS
- Added `postgis/postgis:16-3.4` service and named volume `nexus-postgres-data` to `docker-compose.yml`.
- Configured PostgreSQL and PostGIS environment defaults in `.env.example`.
- Created central application settings module with Pydantic (`services/api/app/config.py`).
- Built SQLAlchemy 2.0 connection engine and session factory (`services/api/app/database.py`).
- Created initial migration `0001_enable_postgis.py` enabling PostGIS extension.

### Added - Phase 02: Environment + Docker
- Configured Node LTS tracking via `.nvmrc`.
- Added `.dockerignore` and service Dockerfiles under `infrastructure/docker/`.
- Configured multi-container orchestration in `docker-compose.yml`.
- Implemented environment health-check script (`scripts/health_check/check_environment.py`).

### Added - Phase 01: Repository Initialization
- Initialized core monorepo directory layout.
- Created explicit Python package markers across all foundational packages.
- Added frontend workspace definitions for `@nexus/command-center` and `@nexus/field-app`.
- Added architectural test suite (`tests/unit/test_repository_structure.py`).

### Added - Prompt 00: Master Project Constitution
- Initialized master project constitution and baseline documentation.
