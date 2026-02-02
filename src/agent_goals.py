from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from src.entity import Agent

class GoalType(Enum):
    SURVIVAL = auto()
    SOCIAL = auto()
    EXPLORE = auto()
    LONG_TERM = auto()

@dataclass
class Goal:
    type: GoalType
    priority: float
    target_id: Optional[str] = None
    metadata: Dict[str, Any] = None

class GoalManager:
    """
    Phase 7: Advanced Goal Hierarchies.
    Manages and prioritizes strategic objectives.
    """
    
    SURVIVAL_CRITICAL = 100.0
    SOCIAL_HIGH = 50.0
    EXPLORE_BASE = 10.0
    
    @staticmethod
    def evaluate_goals(agent: Agent, perception: Dict[str, Any]) -> List[Goal]:
        goals = []
        
        # 1. Survival Check
        energy = perception.get("energy", 100)
        if energy < 40: # SURVIVAL_THRESHOLD in Mind is 30, we start worrying earlier for strategic planning
            priority = (40 - energy) * 2.5 # Scales priority as energy drops
            goals.append(Goal(GoalType.SURVIVAL, priority))
            
        # 2. Social Check (Phase 6 Integration)
        # If we have needy friends and we are rich OR a trusted leader is visible
        visible_agents = perception.get("visible_agents", [])
        if energy > 70: # Richest threshold
            for va in visible_agents:
                if va.get("energy", 100) < 30: # Needy friend
                    goals.append(Goal(GoalType.SOCIAL, GoalManager.SOCIAL_HIGH, target_id=va["id"]))
        
        # Phase 14: Social Learning trigger
        for va in visible_agents:
            trust = agent.trust_scores.get(va["id"], 0.5)
            if trust > 0.6: # Trusted leader
                 goals.append(Goal(GoalType.SOCIAL, 30.0, target_id=va["id"]))
        
        # 3. Exploration (Default)
        goals.append(Goal(GoalType.EXPLORE, GoalManager.EXPLORE_BASE))
        
        # Sort by priority
        goals.sort(key=lambda x: x.priority, reverse=True)
        return goals

    @staticmethod
    def select_top_goal(agent: Agent, perception: Dict[str, Any]) -> Goal:
        goals = GoalManager.evaluate_goals(agent, perception)
        return goals[0] if goals else Goal(GoalType.EXPLORE, 0)
