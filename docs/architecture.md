# Architecture-as-Code v0.1

Mermaid files in `docs/generated/` are derived artifacts, ignored by Git, and must never be edited as architectural truth. Regenerate them with:

```powershell
python -m tests.architecture_flow
```

Factual sources are Component Registry, Lifecycle Ledger, Runtime Audit, Contract Registry, candidate State Machine, Adapter Registry, and Runtime Registry. The Architecture Engine writes:

- `system-fact-architecture.mmd`
- `component-lifecycle.mmd`
- `runtime-topology.mmd`
- `candidate-state.mmd`

Runtime-oriented generated outputs use distinct names: `execution-flow.mmd`, `state-flow.mmd`, and `component-registry.mmd`.

Future design remains separate in [architecture/planned.yaml](../architecture/planned.yaml).
