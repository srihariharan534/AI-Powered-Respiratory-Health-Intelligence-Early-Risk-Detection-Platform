# NEXUS Judge Mode & Evaluation Guide

## 1. Overview & Demonstration Objective

**Judge Mode** is a dedicated presentation and benchmark walkthrough built in **Phase 14**. It enables hackathon judges, technical evaluators, and emergency coordinators to evaluate the complete NEXUS emergency response lifecycle in **3–5 minutes**.

### Core NEXUS Differentiator
> **Decision continuity when physical infrastructure and network connectivity collapse.**

---

## 2. 3-Minute Demonstration Script

| Step | State ID | Title | Key Evaluator takeaway |
|---|---|---|---|
| **1** | `BASELINE` | Baseline Operational State | Digital Twin authority loaded at v42. Roads open, hospital telemetry live. |
| **2** | `FLOOD_SURGE` | Flood Simulation (+1.0m) | Phase 10 Inundation polygon renders. Explicitly watermarked `SIMULATION`. |
| **3** | `BRIDGE_FAILURE` | Bridge B-001 Failure Cascade | Causeway flooded → Bridge marked `FAILED` → Road R-101 marked `BLOCKED`. |
| **4** | `DYNAMIC_REROUTE` | Dynamic Rerouting Triggered | Phase 08 detects severance → Computes Northern Flyover detour ($+1.4\text{ km}$, $+2.7\text{ min}$). |
| **5** | `FIELD_OFFLINE` | Field App Connectivity Lost | Cell towers offline. Field PWA transitions to `OFFLINE` mode. |
| **6** | `OFFLINE_INCIDENT` | Offline Incident Captured | Critical entrapment incident stored locally in IndexedDB without data loss. |
| **7** | `NETWORK_RESTORED_SYNC` | Connectivity Restored & Synced | Gateway reconnects → Event reconciles → Digital Twin bumps to v44. |
| **8** | `WHAT_IF_EVALUATION` | What-If Counterfactual Sandbox | Phase 11 forks state to test hospital capacity drop; live twin remains safe. |

---

## 3. Keyboard Shortcuts & Presentation Controls

- **Next Step**: <kbd>→</kbd> (Right Arrow) or `Next Event` button
- **Previous Step**: <kbd>←</kbd> (Left Arrow) or `Previous` button
- **Reset Demo**: <kbd>R</kbd> or `Reset Demo` button
- **Fullscreen**: `⛶ Fullscreen` toggle button

---

## 4. Safety & State Isolation Guarantees

- **Zero Live State Mutation**: The demo runs against isolated state. Advancing, jumping, or resetting steps never alters the authoritative production Digital Twin database.
- **Unambiguous Data Provenance**: Every state clearly communicates whether it is `REAL DATA`, `SIMULATION`, or `DEMO MODE`.
- **Zero Fabricated Claims**: No artificial "10,000 lives saved" metrics or fake AI animations.
