# Phase 9: Internal Simulation & Forward Modeling

## Overview
Phase 9 implements **forward modeling**, allowing agents to simulate the consequences of their actions in an internal "sandbox" before committing to them. This is a critical step toward recursive self-modeling and proactive agency.

## Objectives
1. **Self-Projection**
   - Predict state changes (Energy, Location) for a sequence of actions.
2. **Success Validation**
   - Evaluate if a generated plan is viable (e.g., "Will I starve before reaching the goal?").
3. **Internal Feedback Loops**
   - If the simulation predicts failure, the agent triggers an immediate replan or goal switch.

## Proposed Changes

### [NEW] src/agent_imagination.py
- `ForwardModel` class:
  - `simulate_plan(agent, plan) -> Dict[str, Any]`: Returns predicted end-state (final energy, final location, success flag).
  - `evaluate_viability(agent, plan) -> bool`: Heuristic check for plan safety.

### [MODIFY] src/agent_mind.py
- Update `decide`:
  - Before executing the first step of a new plan, run `ForwardModel.simulate_plan`.
  - If simulation predicts `energy <= 0`, abort plan and switch to `SURVIVAL` goal immediately.

### [MODIFY] src/sim.py
- Log `IMAGINATION_SUCCESS` or `IMAGINATION_ABORT` events.
