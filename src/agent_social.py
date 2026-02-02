from typing import Dict, Any, List, Optional
from src.entity import Agent, ObjectType
from src.physics import Action, ActionType
from src.agent_meta import AgentMeta

class AgentSocial:
    """
    Phase 6: Social Strategies & Negotiation.
    Handles tracking of other agents and cooperative decision making.
    """
    
    INITIAL_TRUST = 0.5
    TRUST_THRESHOLD = 0.7 # Buffer for safety
    ALTRUISM_ENERGY_THRESHOLD = 70.0  # I only help if I'm rich
    NEEDY_ENERGY_THRESHOLD = 30.0     # Neighbor needs help if energy < 30
    
    @staticmethod
    def update_social_map(agent: Agent, observed_agents: List[Any], current_tick: int):
        pass

    @staticmethod
    def update_seen_agent(agent: Agent, neighbor_id: str, neighbor_data: Dict[str, Any]):
        if neighbor_id not in agent.social_map:
            agent.social_map[neighbor_id] = {}
        agent.social_map[neighbor_id].update(neighbor_data)
        if neighbor_id not in agent.trust_scores:
            agent.trust_scores[neighbor_id] = AgentSocial.INITIAL_TRUST

    @staticmethod
    def record_interaction(agent: Agent, other_id: str, score_delta: float):
        current = agent.trust_scores.get(other_id, AgentSocial.INITIAL_TRUST)
        agent.trust_scores[other_id] = min(1.0, max(0.0, current + score_delta))

    @staticmethod
    def update_reputation(agent: Agent, other_id: str, delta: float):
        current = agent.social_reputations.get(other_id, 0.0)
        agent.social_reputations[other_id] = min(2.0, max(-2.0, current + delta))
        AgentSocial.record_interaction(agent, other_id, delta * 0.5)

    @staticmethod
    def identify_highest_value_info(agent: Agent) -> Dict[str, Any]:
        food_locs = []
        for loc_id, data in agent.cognitive_map.items():
            objs = data.get("objects", [])
            if "FOOD" in objs or "ObjectType.FOOD" in objs:
                food_locs.append(loc_id)
        if not food_locs:
            return {}
        return {"type": "FOOD_LOCATION", "location_id": food_locs[0]}

    @staticmethod
    def decide_cooperation(agent: Agent, perception: Dict[str, Any]) -> Optional[Action]:
        neighbors = perception.get("visible_agents", [])
        if not neighbors:
            return None
        if agent.energy < AgentSocial.ALTRUISM_ENERGY_THRESHOLD:
            return None
        for neighbor in neighbors:
            n_id = neighbor["id"]
            n_energy = neighbor.get("energy", 50)
            trust = agent.trust_scores.get(n_id, AgentSocial.INITIAL_TRUST)
            if n_energy < AgentSocial.NEEDY_ENERGY_THRESHOLD and trust >= AgentSocial.INITIAL_TRUST:
                return Action(ActionType.COMMUNICATE, target_id=n_id)
        return None

    @staticmethod
    def get_observation_to_imitate(agent: Agent, perception: Dict[str, Any]) -> Optional[str]:
        """
        Phase 14: Social Learning.
        Returns a target location ID if a trusted leader is nearby but not in the same room.
        """
        visible_agents = perception.get("visible_agents", [])
        for other in visible_agents:
            if other.get("distance") == 1:
                other_id = other["id"]
                trust = agent.trust_scores.get(other_id, AgentSocial.INITIAL_TRUST)
                if trust >= AgentSocial.TRUST_THRESHOLD:
                    target_loc = other["location"]
                    # Phase 22 Safety Check: Don't follow into known danger
                    if AgentMeta.get_score(agent, target_loc) < -0.5:
                        continue
                    return target_loc
        return None

    @staticmethod
    def generate_story(agent: Agent, perception: Dict[str, Any]):
        loc = perception.get("location", agent.location_id)
        tick = perception.get("tick", agent.last_tick_updated)
        if perception.get("visible_hazards"):
             recent = [s for s in agent.stories if s["topic"] == "HAZARD" and s["location"] == loc and s["tick"] > tick - 20]
             if not recent:
                 story = {"topic": "HAZARD", "location": loc, "tick": tick, "source": agent.id, "veracity": 1.0}
                 agent.stories.append(story)
        if perception.get("visible_coop_food"):
             recent = [s for s in agent.stories if s["topic"] == "FOOD" and s["location"] == loc and s["tick"] > tick - 20]
             if not recent:
                 story = {"topic": "FOOD", "location": loc, "tick": tick, "source": agent.id, "veracity": 1.0}
                 agent.stories.append(story)

    @staticmethod
    def select_story_to_tell(agent: Agent, listener_id: str) -> Optional[Dict[str, Any]]:
        if not agent.stories:
            return None
        return agent.stories[-1]
