# Routing Subsystem Architecture

The Routing Subsystem (`mapeogeo.routing`) consolidates execution planning, dispatch, and work path admissibility.

---

## 1. Primary Operational Question

The routing subsystem is designed to answer a single question:

$$\boxed{\text{Given certified state } G_t \text{ and required work } Q, \text{ what admissible work path should execute?}}$$

---

## 2. Kernel Consumer Boundary

Routing **consumes** the UoW Kernel rather than re-implementing kernel mechanics:
- It does **not** evaluate independent utility models; it queries kernel utility $U$.
- It does **not** create ad-hoc state; it operates on certified state snapshots $G_t$.
- It does **not** bypass certification; all proposed steps must pass kernel boundary $C$.

```text
[Required Work Q] + [Knowledge State G_t]
                  │
                  ▼
         [Work Router Engine]
                  │
                  ├── Admissibility Check (Prerequisites reachable?)
                  ├── Path Optimization (Minimizing execution cost)
                  └── Dispatch Contract Execution
                  │
                  ▼
         [Admissible Execution Plan]
```

---

## 3. Core Capabilities

1. **Path Admissibility**: A routing path is admissible if and only if all prerequisite nodes along the path exist in $G_t$ or are certified antecedent steps in the plan.
2. **Backpressure & Power Control**: The router modulates throughput when candidate pools exceed processing budget, preventing combinatorial explosion.
3. **Dispatch Contracts**: Formal preconditions and postconditions bound to execution steps, ensuring deterministic dispatch across heterogeneous execution backends.
