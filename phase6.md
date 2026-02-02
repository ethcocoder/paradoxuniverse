# Phase 6: Social Strategies & Negotiation - Implementation Plan

## Overview
Phase 6 introduces **social reasoning and negotiation** for agents. Agents will now:

- Track other agents’ positions, energy levels, and known resources.
- Share information and coordinate for mutual benefit.
- Negotiate for food, tools, or guidance.
- Adjust personal plans based on peers’ actions.

This enhances collaboration, avoids conflict, and enables group survival strategies.

---

## Goals
1. **Social Awareness**
   - Maintain a `social_map` of known agents.
   - Track trustworthiness, cooperation history, and visible actions.

2. **Negotiation & Cooperation**
   - Request assistance when low on resources.
   - Share food or critical information with trusted agents.
   - Evaluate trade-offs: energy cost vs benefit.

3. **Strategic Multi-Agent Planning**
   - Integrate peers’ plans into personal planning.
   - Avoid resource conflicts.
   - Coordinate exploration to optimize coverage.

---

## Proposed Changes

### 1. New Module
**File:** `src/agent_social.py`  

**Responsibilities:**
- `AgentSocial` class:
  - `update_social_map(agent_id, location, energy, resources)`: Track other agents.
  - `evaluate_trust(agent_id) -> float`: Compute cooperation likelihood.
  - `propose_trade(agent_id, offer, request)`: Handle resource negotiation.
  - `decide_cooperation(agent, world_state) -> Action`: Determine whether to help another agent or request help.

---

### 2. Modifications to Agent Class
**File:** `src/entity.py`  

Add:
```python
class Agent:
    social_map: Dict[str, Dict] = {}  # Tracks other agents
    trust_scores: Dict[str, float] = {}  # Trust level per agent
