# Contributing to NEXUS

Thank you for your interest in contributing to **NEXUS — Offline-First AI Flood Response & Emergency Decision Platform**.

This project adheres to a strict architectural roadmap and high engineering standards to maintain life-critical software reliability.

---

## 1. Architectural Guardrails

Before contributing, please read the [Master Project Constitution](README.md) and note:
1. **Digital Twin as Single Authority**: The `digital_twin/` package owns central state concepts and transitions. Do not introduce competing state layers.
2. **Canonical Synchronization**: Follow `services/sync/sync_protocol.md`.
3. **No Feature Creep**: Do not introduce unrequested frameworks, speculative microservices, blockchain, or uncalibrated chat wrappers.
4. **Honest AI & Evaluation**: All evaluation metrics must be derived from runnable benchmark suites in `evaluation/`. No invented performance statistics.

---

## 2. Development Workflow

1. Check out a descriptive feature branch:
   ```bash
   git checkout -b feature/phase-xx-description
   ```
2. Maintain consistent code style:
   - Python: `snake_case`, typed annotations, `ruff` / `black` formatting.
   - React / TypeScript: `kebab-case` directories, strict typing, clean separation of concerns.
3. Add unit and integration tests under `tests/`.
4. Run validation checks before committing:
   ```bash
   make test
   ```

---

## 3. Commit Guidelines

Use structured conventional commit messages:
- `feat(sync): implement conflict resolution strategy`
- `fix(routing): prevent null reference on severed bridge graph edge`
- `docs(judges): update scenario walkthrough steps`
