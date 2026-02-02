import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Set, Any, Optional
from enum import Enum, auto

@dataclass
class Entity:
    """
    Base class for all entities in the simulation.
    Entities are data containers with a unique immutable ID.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

@dataclass
class Agent(Entity):
    """
    An agent capable of action.
    """
    name: str = "Unnamed Agent"
    location_id: str = ""
    energy: int = 100
    is_alive: bool = True
    
    # Phase 2: Memory & Minds
    memory: List[Dict[str, Any]] = field(default_factory=list) # Short-term memory buffer
    visited_locations: Set[str] = field(default_factory=set)   # For exploration heuristics
    
    # Phase 3: Communication & Mapping
    cognitive_map: Dict[str, Dict[str, Any]] = field(default_factory=dict) # Internal model of world: {loc_id: {data}}
    message_queue: List[Dict[str, Any]] = field(default_factory=list)      # Incoming messages
    
    # Phase 4: Reflection
    action_history: List[Dict[str, Any]] = field(default_factory=list)     # History of actions/results
    reflection_score: Dict[str, float] = field(default_factory=dict)       # Heuristic scores (e.g. {"loc_id_efficiency": 0.5})

    # Phase 5: Planning
    plan_queue: List[Any] = field(default_factory=list)                    # List[Action] (Sequence of planned actions)
    planned_target: str = None                                             # ID of the current plan's goal

    # Phase 6: Social
    social_map: Dict[str, Dict] = field(default_factory=dict)              # Known agents: {agent_id: {loc, energy, last_seen}}
    trust_scores: Dict[str, float] = field(default_factory=dict)           # Trust metric: {agent_id: 0.0 to 1.0}

    # Phase 7: Goals
    current_goal: str = "EXPLORE"                                          # Current strategic goal
    goal_history: List[str] = field(default_factory=list)                  # History of strategic shifts

    # Phase 8: Long-Term Memory
    spatial_patterns: Dict[str, Dict[str, float]] = field(default_factory=dict) # {loc_id: {food_hits: 1, total_visits: 5}}
    social_reputations: Dict[str, float] = field(default_factory=dict)     # {agent_id: aggregated_score}
    stories: List[Dict[str, Any]] = field(default_factory=list) # Phase 17: Cultural Knowledge
    
    # Phase 12: Caching & Territoriality
    inventory: List['Object'] = field(default_factory=list)               # Items carried by the agent
    home_location_id: Optional[str] = None                                # Chosen home base

    # Phase 14: Social Learning
    last_action: Optional[Any] = None                                     # Most recent Action committed

    # Track the last tick updated to help with debugging/synchronization
    last_tick_updated: int = 0

class ObjectType(Enum):
    FOOD = auto()
    BARRIER = auto()
    TOOL = auto()
    HAZARD = auto() # Phase 13: High-damage environmental static danger
    COOP_FOOD = auto() # Phase 15: Requires multiple agents to extract
    OBSTACLE = auto() # Phase 20: Requires tool to bypass

@dataclass
class Object(Entity):
    """
    A passive object in the world.
    """
    type: ObjectType = ObjectType.FOOD
    value: int = 0  # e.g., energy value for food
    location_id: str = ""
    # Phase 15
    required_agents: int = 1
    # Phase 20
    tool_required: Optional[str] = None # Name of tool type needed (e.g. "KEY")
    tool_type: Optional[str] = None # If type is TOOL, this is the specific type name (e.g. "KEY")
