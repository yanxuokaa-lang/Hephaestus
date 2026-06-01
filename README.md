# Hephaestus v0.1.0

Hephaestus is a simulation-first robotic-agent project. This public repository publishes a
stable core-code slice of the Phase 1C architecture without exposing the private working
process behind it.

## Snapshot Scope

This snapshot is centered on source owners, not on process artifacts:

- `tool` contracts for robot, perception, safety, deterministic simulation, and scene truth
- `atom` contracts for motion, manipulation, perception, and utility actions
- `skill` policy code for grasp and place strategy surfaces
- `task` contracts for tool registration and public proof cases
- a small CLI for inspecting the public bundle

## Public Core Source Files

- `hephaestus/tool/types.py`
- `hephaestus/tool/robot_arm.py`
- `hephaestus/tool/perception.py`
- `hephaestus/tool/safety.py`
- `hephaestus/tool/simulation.py`
- `hephaestus/tool/scene_carrier.py`
- `hephaestus/tool/simulated_perception.py`
- `hephaestus/tool/sim_arm.py`
- `hephaestus/atom/motion.py`
- `hephaestus/atom/manipulation.py`
- `hephaestus/atom/perception.py`
- `hephaestus/skill/grasp_policy.py`
- `hephaestus/skill/place_policy.py`
- `hephaestus/task/registry.py`
- `hephaestus/task/proof_cases.py`

## Not Included

- internal working notes
- private review records
- presentation runtime internals
- runtime memory stores
- raw capture artifacts or recordings

## Install

```bash
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

## Inspect The Public Bundle

```bash
python -m hephaestus.cli.main list-core-files --json
python -m hephaestus.cli.main list-proof-cases --json
python -m hephaestus.cli.main show-scene-carrier tabletop_organization_v1 --json
```

## Validate

```bash
git diff --check
python -m pytest -q
```

## Docs

- [docs/architecture.md](docs/architecture.md)
- [docs/system-architecture.md](docs/system-architecture.md)
- [docs/phase1c-closure.md](docs/phase1c-closure.md)
