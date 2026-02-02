# Phase 4: Self-Reflection & Meta-Cognition - Implementation Plan

## Goal Description
Enable agents to analyze their own history, evaluate past actions, and adjust future decision-making. This allows:

- Reflection on previous actions and outcomes
- Meta-cognition: reasoning about their own decision patterns
- Improved survival and exploration through learned heuristics (non-AI, rule-based)

---

## Proposed Changes

### Structure
New module for reflection logic.


### Components

**1. src/entity.py**
- Update `Agent` class:
  - `action_history: List[Dict]` – stores past actions with tick, result, and context
  - `reflection_score: Dict[str, float]` – evaluates effectiveness of actions (e.g., energy efficiency, exploration success)

**2. src/agent_meta.py**
- `AgentMeta` class:
  - `reflect(agent) -> Dict`  
    - Analyze `action_history`
    - Compute reflection metrics (e.g., most efficient moves, wasted energy)
  - `adjust_decisions(agent) -> None`  
    - Update decision priorities based on reflection
    - Example: avoid repeatedly visiting empty locations

**3. src/agent_mind.py**
- Update `decide()`:
  - Incorporate reflection feedback from `AgentMeta`
  - Prioritize actions based on meta-evaluation

**4. src/sim.py**
- Tick loop additions:
  - After `Act Phase`:
    - Call `AgentMeta.reflect(agent)`
    - Update `agent.reflection_score`
    - Feed into next tick's `decide()` for improved behavior

---

## Verification Plan

### Automated Tests
- **Reflection Storage:** Verify `action_history` is correctly maintained
- **Reflection Metrics:** Test `reflection_score` updates appropriately
- **Meta-Decision Improvement:** Agents should reduce repeated mistakes (e.g., unnecessary moves or failed attempts)

### Manual Verification
- Run simulation with multiple agents
- Observe logs for:
  - Reflection events: `{ "type": "REFLECTION", "agent_id": "...", "insight": "..."}`
  - Decision adjustments based on past experience
- Example scenario:
  - Agent repeatedly visits Room B (no food)
  - After reflection, agent deprioritizes Room B in exploration

---

## Next Steps
Phase 5: Advanced Planning & Anticipatory Behavior  
- Agents will simulate potential future states to plan multi-step strategies.
