# System Architecture

The public Phase 1C snapshot follows a narrow, inspection-first runtime shape:

```text
CLI
  -> task contracts
  -> skill policies
  -> atom primitives
  -> tool contracts and deterministic simulation
```

The repository keeps the stable owner files visible so an external reader can trace the main
system boundaries without importing the private working layers.

## Public Inspection Commands

- `list-core-files`
- `list-proof-cases`
- `show-scene-carrier`
- `show-grasp-policy`
