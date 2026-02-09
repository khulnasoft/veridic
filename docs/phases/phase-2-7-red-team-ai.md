# Phase 2.7 — Continuous Red-Team AI (Preview)

> **Status**: Preview Scaffolded  
> **Goal**: Turn Veridic into a living red team that intelligently attacks itself.

---

## **Current Implementation**

We have scaffolded the **Phase 2.7** infrastructure as a bridge from Phase 2.6. This enables autonomous attack planning and coverage analysis while maintaining strict safety controls.

### **1. Attack Planning (`attack_planner.py`)**
- Derives new attack strategies based on existing findings.
- Prioritizes targets by severity.
- Hash-locked planning for reproducibility.

### **2. Strategy Mutation (`strategy_mutator.py`)**
- Safely mutates payloads (case-swapping, encoding, prefixes).
- Deterministic mutation pipeline.

### **3. Coverage Analysis (`coverage_analyzer.py`)**
- Correlates AST data with finding locations.
- Identifies "Dark Spots" (untested code paths with external input).
- Focuses red-team efforts on high-risk gaps.

### **4. Red-Team Loop (`redteam_loop.py`)**
- Main orchestrator for continuous testing.
- **Safety Kill-Switch**: Disabled by default (`active=False`).
- Logs all iteration attempts for human auditing.

---

## **Safety & Determinism Rules**

| Target | Rule |
| :--- | :--- |
| **Autonomy** | Always requires an explicit `loop.enable()` call. |
| **Memory** | Tracks what fails (negative proof) to avoid infinite loops. |
| **Reproducibility** | All mutation seeds are locked and logged. |
| **Impact** | Limited to non-destructive payloads in Phase 2.6 sandboxes. |

---

## **Next Steps**

1. **Strategy Persistence**: Save attack history to the Phase 2.5 aggregator.
2. **AI-Driven Mutation**: Use LLM to suggest intelligent payload mutations.
3. **Graph-Based Propagation**: Hook into the Phase 1 Knowledge Graph to find reachable dataflow paths for new attacks.
4. **Kill-Switch API**: Expose the loop control to the gRPC server.

---

*This phase transforms Veridic from a security tool into an autonomous security operator.*
