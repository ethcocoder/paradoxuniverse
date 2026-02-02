from typing import Dict, Any, List, Optional
from src.entity import Agent
from src.physics import ActionType

class MemoryAnalyzer:
    """
    Phase 8: Long-Term Strategic Memory & Pattern Recognition.
    Analyzes historical data to build models of the environment and social actors.
    """
    
    @staticmethod
    def update_patterns(agent: Agent, current_perception: Dict[str, Any]):
        """
        Updates spatial frequency and resource probability based on current observation.
        """
        loc_id = current_perception["location"]
        if loc_id not in agent.spatial_patterns:
            agent.spatial_patterns[loc_id] = {"total_visits": 0.0, "food_hits": 0.0}
        
        patterns = agent.spatial_patterns[loc_id]
        if "visits" in patterns: # Migration/Fix for old data if any
             patterns["total_visits"] = patterns.pop("visits", 0.0)
             
        patterns["total_visits"] += 1.0
        
        if current_perception.get("visible_food"):
            patterns["food_hits"] += 1.0

    @staticmethod
    def get_food_hit_rate(agent: Agent, loc_id: str) -> float:
        if loc_id not in agent.spatial_patterns:
            return 0.0
        p = agent.spatial_patterns[loc_id]
        visits = p.get("total_visits", p.get("visits", 0.0))
        if visits == 0:
             return 0.0
        return p["food_hits"] / visits

    @staticmethod
    def predict_resource_location(agent: Agent) -> Optional[str]:
        """
        Returns the location with the highest historical food hit rate.
        Only considers locations with enough significance.
        """
        best_loc = None
        best_rate = -1.0
        
        for loc_id, stats in agent.spatial_patterns.items():
            visits = stats.get("total_visits", stats.get("visits", 0.0))
            if visits < 1:
                continue
            
            rate = stats["food_hits"] / visits
            if rate > best_rate and rate > 0:
                best_rate = rate
                best_loc = loc_id
                
        return best_loc

    @staticmethod
    def update_social_reputation(agent: Agent, sender_id: str, delta: float):
        """
        Aggregates trust changes into a persistent reputation.
        """
        current = agent.social_reputations.get(sender_id, 0.5)
        # Slower moving than trust? Or just a mirror?
        agent.social_reputations[sender_id] = min(1.0, max(0.0, current + delta))
