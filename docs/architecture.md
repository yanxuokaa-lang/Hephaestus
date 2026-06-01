# Public Architecture

Hephaestus is organized around four owner layers.

## tool

The tool layer owns the primitive contracts:

- robot-arm abstraction
- perception abstraction
- deterministic simulation seam
- safety checks
- scene-carrier truth for the public tabletop scenario

## atom

The atom layer owns reusable action primitives. In this snapshot the stable public atoms cover:

- motion
- manipulation
- perception
- utility

## skill

The skill layer owns strategy code that sits above atoms and below task orchestration. The
public snapshot keeps the grasp and place policy owners visible because they are stable and
useful without exposing private process surfaces.

## task

The task layer owns the public tool-registry seam and the proof-case contract used to describe
the tabletop Phase 1C scenario.
