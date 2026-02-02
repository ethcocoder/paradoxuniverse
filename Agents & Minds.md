# Phase 2 — Agents & Minds

## Objective
Introduce active agent behavior, short-term memory, and proto-goal-directed decision-making
without introducing AI or learning. This lays the foundation for self-model emergence.

---

## Components

### 1. Agent Perception
- Gather local environment state (current location, objects, neighboring rooms)
- Output structured perception dict:
  ```python
  perception = {
      "location": "Room_B",
      "objects": ["Food_1"],
      "neighbors": ["Room_A", "Room_C"],
      "energy": 15
  }
