from typing import Dict, Any, List, Set
from collections import Counter
from src.entity import Agent
from src.physics import ActionType

class AgentMeta:
    """
    Phase 4: Meta-Cognition.
    Analyzes agent history to operationalize 'Reflection'.
    """
    
    REFLECTION_WINDOW = 20
    INEFFICIENCY_PENALTY = 0.5
    
    @staticmethod
    def reflect(agent: Agent):
        """
        Analyzes recent history and updates heuristic scores.
        """
        # Look at last N entries
        history = agent.action_history[-AgentMeta.REFLECTION_WINDOW:]
        if not history:
            return

        # 1. Identify "Stuck" loops or ping-ponging using counters
        # We look at "MOVE" actions and their target
        move_targets = [
            entry["action"].target_id 
            for entry in history 
            if entry.get("action") and entry["action"].type == ActionType.MOVE
        ]
        
        target_counts = Counter(move_targets)
        
        # 2. Update Reflection Scores
        # If we visit a place too often in short window, penalize it
        for loc_id, count in target_counts.items():
            if count > 3: # HEURISTIC: Visited >3 times in last 20 ticks
                current_score = agent.reflection_score.get(loc_id, 0.0)
                # Apply penalty
                agent.reflection_score[loc_id] = current_score - AgentMeta.INEFFICIENCY_PENALTY
            # Else could slowly decay penalty (forgive)?
            
        # 3. Detect "Fruitless" exploration
        # e.g. Moved to X, outcome was success, but gained no energy/info? 
        # (This is harder to check without deeper history context, keeping it simple for now)

    @staticmethod
    def get_score(agent: Agent, loc_id: str) -> float:
        """Returns the reflection score for a location (Default 0)."""
        return agent.reflection_score.get(loc_id, 0.0)

    @staticmethod
    def update_score(agent: Agent, loc_id: str, delta: float):
        """Phase 13: Manually update a score (e.g. from Alarms)."""
        current = agent.reflection_score.get(loc_id, 0.0)
        agent.reflection_score[loc_id] = current + delta
