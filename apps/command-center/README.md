# NEXUS Command Center

The **NEXUS Command Center** is the primary operational interface for District Emergency Operations Center (EOC) coordinators, incident supervisors, and emergency decision-makers.

Built in **Phase 12 (Command Center Foundation)**, this application provides an offline-first, safety-oriented web shell ready for Phase 13 (Live GIS Dashboard) and Phase 14 (Judge Mode).

---

## Architecture & Principles

1. **Information Hierarchy**: Prioritizes `RISK` → `DECISION` → `ACTION` → `CHANGE`. Avoids generic SaaS or flashy cyberpunk aesthetic in favor of clear, mission-critical operational clarity.
2. **Data Mode Clarity**: The interface clearly and prominently distinguishes `REAL DATA` from `SIMULATION` and `DEMO MODE`. Simulation models execute in isolated sandboxes and never mutate authoritative Digital Twin states.
3. **Digital Twin Authority**: Integrates directly with the versioned Digital Twin state authority (`State Version: X`). Stale or unavailable backend states are reported honestly without fabricated numbers.
4. **Resilient API Client**: Centralized typed HTTP client handling network timeouts, offline states, and structured errors (`ApiError`).

---

## Route Overview

| Route | View | Status |
|---|---|---|
| `/dashboard` | District EOC Operational Overview | Available (Foundation) |
| `/incidents` | Triaged Emergency Incidents | Available (Foundation) |
| `/simulation` | What-If Counterfactual Scenario Launcher | Available (Foundation) |
| `/digital-twin` | State Authority & Entity Registry | Available (Foundation) |
| `/hospitals` | Medical Facilities & Triage Capacity | Active (Phase 16) |
| `/shelters` | Evacuation Shelters & Relief Camps | Active (Phase 16) |
| `/vulnerability` | Demographic Priority & Flood Risk Baseline | Active (Phase 17) |
| `/recommendations` | Decision Support Pipeline & Human Approval | Phase 20 Foundation |
| `/audit` | Provenance Ledger & Action Log | Phase 19 Foundation |
| `/judge-mode` | Evaluator Mode & Benchmark Proofs | Active (Phase 14) |

---

## Project Structure

```text
apps/command-center/
├── public/
├── src/
│   ├── components/
│   │   ├── layout/       # Header, Sidebar, Footer, AppLayout
│   │   └── ui/           # StatusIndicator, SeverityBadge, DataModeBadge, Card, Button, FeedbackStates
│   ├── context/          # AppContext (ConnectionStatus, DataMode, StateVersion)
│   ├── pages/            # Dashboard, Incidents, Simulation, DigitalTwin, OperationalPages
│   ├── services/         # Centralized API client and endpoint adapters
│   ├── types/            # TypeScript data contracts and error models
│   ├── App.tsx           # React Router DOM configuration
│   ├── index.css         # Operational dark theme tokens and responsive grid layout
│   └── main.tsx          # Application bootstrap
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## Running Locally

### Development Server
```bash
npm run dev
```

### Production Build
```bash
npm run build
```

### Running Test Suite
```bash
npm test
```
All UI primitives, layout navigation, and API client failure modes are covered with Vitest and `@testing-library/react`.
