# Phase 5: Advanced Planning & Anticipatory Behavior - Implementation Plan

## Goal Description
Enable agents to simulate potential future states and plan multi-step strategies. This allows:

- Anticipating consequences of actions
- Optimizing exploration routes
- Prioritizing high-reward outcomes (food, new rooms)
- Combining self-reflection with forward-looking planning

---

## Proposed Changes

### Structure
New module for planning logic.


### Components

**1. src/entity.py**
- Update `Agent` class:
  - `plan_queue: List[Action]` – stores multi-step planned actions
  - `planned_target: Optional[str]` – current planning focus

**2. src/agent_planner.py**
- `AgentPlanner` class:
  - `simulate(agent, steps: int) -> List[Action]`  
    - Predict outcomes of candidate actions
    - Estimate energy, reachability, and reward
  - `generate_plan(agent) -> List[Action]`  
    - Select optimal sequence of actions
    - Push to `plan_queue`

**3. src/agent_mind.py**
- Update `decide()`:
  - Check `plan_queue` first
  - Follow pre-planned steps if available
  - Otherwise, generate new plan via `AgentPlanner`

**4. src/sim.py**
- Tick loop additions:
  - Perceive → Decide → Execute → Plan
  - Log planned actions with type `"PLAN"` and expected outcomes

---

## Verification Plan

### Automated Tests
- **Plan Generation:** Verify plans respect energy constraints and predicted rewards
- **Execution Fidelity:** Agents follow plan correctly, adjusting for unexpected events
- **Efficiency Improvement:** Agents reach goals faster than random or greedy behavior

### Manual Verification
- Run simulation with multiple agents in complex map
- Observe logs:
  - Reflection events (`REFLECTION`) integrate with planning
  - Planned actions (`PLAN`) followed correctly
  - Outcomes match predicted simulations

---

## Next Steps
Phase 6: Social Strategies & Negotiation  
- Agents will coordinate plans, resolve conflicts, and optimize group-level objectives.
