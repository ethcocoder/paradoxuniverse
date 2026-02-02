# Phase 8: Long-Term Strategic Memory & Pattern Recognition

## Overview
Phase 8 enables agents to learn from historical data over long durations. Instead of just reacting to the current state or a short memory buffer, agents will develop **Environmental Models** and **Social Reputations**.

## Goals
1. **Environmental Modeling**
   - Track `food_discovery_count` per location.
   - Calculate `probability_of_resource` for unmapped or currently empty rooms.
2. **Social Reputation**
   - Aggregate trust delta over lifetime into a `social_standing` score.
   - Remember which agents provide valid vs invalid information.
3. **Pattern-Based Navigation**
   - When "Hungry", prioritize rooms with the highest historical food hit-rate if no food is currently visible.

## Proposed Changes

### [MODIFY] src/entity.py
- Add `long_term_memory`: Dict with `spatial_patterns` and `social_reputations`.

### [NEW] src/agent_memory_pro.py
- `MemoryAnalyzer` class:
  - `update_patterns(agent, history_chunk)`: Processes action history to update hit-rates.
  - `predict_resource_location(agent, resource_type)`: Returns the best guess room.

### [MODIFY] src/agent_mind.py
- Update `decide`:
  - If Goal is SURVIVAL and no food is in Map, consult `MemoryAnalyzer` for a "Best Guess" location.
