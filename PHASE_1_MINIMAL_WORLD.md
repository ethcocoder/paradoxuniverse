# Phase 1 — Minimal World, Time, and Rules

## Objective
Create a minimal but consistent simulated universe where agents can exist,
perceive, act, and experience consequences over time.

This phase intentionally avoids intelligence, learning, or language.
The goal is to establish causality and persistence.

---

## Design Principles
- Text-based only (no graphics)
- Deterministic rules
- Discrete time (ticks)
- Small state space
- Fully observable for debugging

---

## World Model

### World Components
- Locations (nodes or rooms)
- Objects (food, obstacles, tools)
- Global time counter
- Event log

### Example Locations
- Room_A
- Room_B
- Room_C

### Example Objects
- Food (+energy)
- Empty space
- Barrier

---

## Rules Engine

Rules define physics-like constraints:

- Moving between locations costs energy
- Eating restores energy
- Doing nothing causes boredom penalty
- Energy ≤ 0 → agent failure state

Rules MUST be centralized and immutable.

---

## Time System

- World advances in discrete ticks
- Each tick:
  1. World updates
  2. Events are processed
  3. Logs are written

Time is required for:
- Memory
- Cause → effect
- Identity continuity

---

## Success Criteria

Phase 1 is complete when:
- The world runs for 1000+ ticks without errors
- State changes are consistent and explainable
- Logs clearly show cause → effect chains

No intelligence is required yet.

---

## Explicit Non-Goals
- No learning
- No self-awareness
- No language
- No optimization

This phase is infrastructure only.
