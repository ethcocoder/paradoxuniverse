# Phase 3: Communication & Advanced Mapping

## Goal Description
Introduce multi-agent communication, shared world representation, and advanced exploration strategies. This phase enables agents to collaboratively build cognitive maps of the world and make higher-level decisions based on shared knowledge.

---

## Objectives
1. **Communication**: Allow agents to share observations about locations, objects, and hazards.
2. **Cognitive Map**: Each agent maintains an internal map of the world.
3. **Exploration Strategy**: Use curiosity and boredom to guide movement toward unknown locations.
4. **Proto-Collaboration**: Agents can prioritize exploration vs survival with information from other agents.
5. **Logging**: Extend JSONL to track communication events and map updates.

---

## Proposed Changes

### 1. New Component
- `src/agent_communication.py`  
  Responsibilities:
  - Send/receive messages between agents.
  - Update internal cognitive maps with received data.
  - Handle message delay/energy cost simulation (optional).

### 2. Entity Updates
- `src/entity.py`:
  - Add `cognitive_map: Dict[str, Dict] = field(default_factory=dict)` to `Agent`.
    - Stores known locations, objects, and last observed tick.
  - Add `message_queue: List[Dict] = field(default_factory=list)` for incoming communications.

### 3. Mind Updates
- `src/agent_mind.py`:
  - Add `decide_communication(agent)` method.
  - When energy > threshold and new information exists → broadcast.
  - Update `decide(agent, perception)` to consider received messages:
    - Prefer unexplored or high-survival-value locations from other agents’ info.

### 4. Simulation Updates
- `src/sim.py`:
  - During each tick:
    1. Perception
    2. Update internal map from received messages
    3. Decide action (MOVE, CONSUME, WAIT, COMMUNICATE)
    4. Apply action in physics engine
    5. Log perception, decision, effect, and communication events

### 5. Logging
- `src/logger.py`:
  - Add `type: "COMMUNICATION"` events
  - Track:
    - Sender ID
    - Receiver IDs
    - Shared data
    - Tick timestamp

---

## Verification Plan

### Automated Tests
1. **Communication Test**:
    - Agent A observes food.
    - Agent A broadcasts.
    - Agent B receives and updates cognitive map.
    - Assert Agent B’s map contains the food location.
2. **Exploration Test**:
    - Agents move to unknown locations based on cognitive map guidance.
3. **Energy Cost Test**:
    - Communication consumes energy if implemented.
4. **Map Consistency Test**:
    - Cognitive maps converge over multiple ticks when communication is reliable.

### Manual Verification
- Run `main.py` with multiple agents.
- Inspect JSONL logs for:
  ```json
  {
    "type": "COMMUNICATION",
    "tick": 12,
    "sender_id": "agent_A",
    "receiver_ids": ["agent_B"],
    "shared_data": {"Room_X": {"food": 50}}
  }
