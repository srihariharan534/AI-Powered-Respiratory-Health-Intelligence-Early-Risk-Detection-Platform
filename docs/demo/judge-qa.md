# NEXUS Judge Q&A & Technical Defense

## Common Technical Questions & Honest Architecture Answers

### Q1: Why is offline-first an absolute core requirement?
**Answer**: During catastrophic flood disasters, cellular base stations and fiber backhauls routinely fail. If field officers cannot record water depths or rescue entrapments locally, critical operational ground truth is lost. NEXUS stores events locally (in IndexedDB) and deterministically reconciles them via Merkle hashes upon reconnection.

### Q2: How does NEXUS prevent hallucinated or unsafe AI actions?
**Answer**: 
1. **Digital Twin as Operational Authority**: Decisions are grounded in versioned state, not unstructured LLM context.
2. **Deterministic Modeling**: Flood inundation (Phase 10) and Dynamic Rerouting (Phase 08) use mathematical graph theory (A*/Dijkstra) and elevation models, not probabilistic hallucinations.
3. **Mandatory Human-in-the-Loop**: High-consequence actions require explicit coordinator approval with confidence intervals and trade-off explanations.

### Q3: How does the system handle route failures when roads submerge?
**Answer**: Phase 08 Dynamic Rerouting applies a non-destructive operational state overlay. When bridge failure or flood depth breaches vehicle clearance thresholds, affected graph edges are invalidated. The router calculates alternate paths and produces structured delta metrics ($+1.4\text{ km}$, $+2.7\text{ min}$) with natural language explanations.

### Q4: How is What-If simulation isolated from live operational state?
**Answer**: Phase 11 forks the Digital Twin state into an isolated copy-on-write sandbox. Simulations evaluate counterfactual questions ("What if Hospital H-002 capacity drops to 0?") without mutating the authoritative live state version.
