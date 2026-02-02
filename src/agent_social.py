from typing import Dict, Any, List, Optional
from src.entity import Agent
from src.physics import Action, ActionType

class AgentSocial:
    """
    Phase 6: Social Strategies & Negotiation.
    Handles tracking of other agents and cooperative decision making.
    """
    
    INITIAL_TRUST = 0.5
    TRUST_THRESHOLD = 0.6
    ALTRUISM_ENERGY_THRESHOLD = 70.0  # I only help if I'm rich
    NEEDY_ENERGY_THRESHOLD = 30.0     # Neighbor needs help if energy < 30
    
    @staticmethod
    def update_social_map(agent: Agent, observed_agents: List[Any], current_tick: int):
        """
        Updates the agent's internal social map with currently visible agents.
        observed_agents: List of Agent objects (or dicts from perception?)
        Actually perception usually sends IDs or partial data. 
        In Sim.py/AgentMind.perceive, we can pass actual Agent objects or just data.
        Let's assume we pass the perception data or world access.
        """
        # For simplicity, let's assume 'perception' passed to AgentMind contains detailed info 
        # about neighbors if we are implementing realistic sensing.
        # But 'perceive' currently only returns IDs of neighbors.
        # Phase 6 implies improved perception of agents.
        # We will handle the data extraction in AgentMind and pass it here.
        pass

    @staticmethod
    def update_seen_agent(agent: Agent, neighbor_id: str, neighbor_data: Dict[str, Any]):
        """
        Updates specific agent entry.
        neighbor_data: {loc, energy, etc.}
        """
        if neighbor_id not in agent.social_map:
            agent.social_map[neighbor_id] = {}
        
        # Update fields
        agent.social_map[neighbor_id].update(neighbor_data)
        
        # Init trust if new
        if neighbor_id not in agent.trust_scores:
            agent.trust_scores[neighbor_id] = AgentSocial.INITIAL_TRUST

    @staticmethod
    def record_interaction(agent: Agent, other_id: str, score_delta: float):
        """
        Updates trust based on interaction (e.g. received useful info).
        """
        current = agent.trust_scores.get(other_id, AgentSocial.INITIAL_TRUST)
        agent.trust_scores[other_id] = min(1.0, max(0.0, current + score_delta))

    @staticmethod
    def update_reputation(agent: Agent, other_id: str, delta: float):
        """
        Phase 16: Updates the reputation of another agent.
        Reputation is tracked in agent.social_reputations.
        """
        current = agent.social_reputations.get(other_id, 0.0)
        agent.social_reputations[other_id] = min(2.0, max(-2.0, current + delta))
        
        # Reputation also slightly influences trust
        AgentSocial.record_interaction(agent, other_id, delta * 0.5)

    @staticmethod
    def identify_highest_value_info(agent: Agent) -> Dict[str, Any]:
        """
        Phase 11: Identifies the most useful piece of info we have.
        Currently: The location of the nearest food in our cognitive map.
        """
        food_locs = []
        for loc_id, data in agent.cognitive_map.items():
            objs = data.get("objects", [])
            if "FOOD" in objs or "ObjectType.FOOD" in objs:
                food_locs.append(loc_id)
        
        if not food_locs:
            return {}
            
        # Return the first one for now (or nearest to current? simplified: the first)
        return {"type": "FOOD_LOCATION", "location_id": food_locs[0]}

    @staticmethod
    def decide_cooperation(agent: Agent, perception: Dict[str, Any]) -> Optional[Action]:
        """
        Decides if we should perform a social action (Help/Trade).
        Returns Action or None.
        """
        # 1. scan neighbors
        neighbors = perception.get("visible_agents", []) # We need to ensure perception has this
        
        if not neighbors:
            return None
            
        # 2. Check overlap: Am I rich?
        if agent.energy < AgentSocial.ALTRUISM_ENERGY_THRESHOLD:
            return None
            
        # 3. Look for needy friends
        for neighbor in neighbors:
            n_id = neighbor["id"]
            n_energy = neighbor.get("energy", 50)
            
            # Trust Check
            trust = agent.trust_scores.get(n_id, AgentSocial.INITIAL_TRUST)
            
            if n_energy < AgentSocial.NEEDY_ENERGY_THRESHOLD and trust >= AgentSocial.INITIAL_TRUST:
                # They are needy and at least neutral/trusted.
                # Action: Share Info (Communicate)
                # We assume communicating helps them (gives them map data to find food).
                # We also assume 'COMMUNICATE' is the action for this.
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
            # Only follow if they are in a DIFFERENT room (distance 1)
            # If they are in the SAME room, we are already with them.
            if other.get("distance") == 1:
                other_id = other["id"]
                trust = agent.trust_scores.get(other_id, AgentSocial.INITIAL_TRUST)
                
                if trust >= AgentSocial.TRUST_THRESHOLD:
                    # They are in an adjacent room. Let's follow!
                    return other["location"]
        
        return None

    @staticmethod
    def generate_story(agent: Agent, perception: Dict[str, Any]):
        """
        Phase 17: Creates a story from impactful events.
        """
        loc = perception["location"]
        tick = perception["tick"]
        
        # 1. Hazard Story
        if perception.get("visible_hazards"):
             # Check if we already have this story recently
             recent = [s for s in agent.stories if s["topic"] == "HAZARD" and s["location"] == loc and s["tick"] > tick - 20]
             if not recent:
                 story = {
                     "topic": "HAZARD",
                     "location": loc,
                     "tick": tick,
                     "source": agent.id, # Primary observation
                     "veracity": 1.0
                 }
                 agent.stories.append(story)
        
        # 2. Food Story (Large amount or coop)
        if perception.get("visible_coop_food"):
             recent = [s for s in agent.stories if s["topic"] == "FOOD" and s["location"] == loc and s["tick"] > tick - 20]
             if not recent:
                 story = {
                     "topic": "FOOD",
                     "location": loc,
                     "tick": tick,
                     "source": agent.id,
                     "veracity": 1.0
                 }
                 agent.stories.append(story)

    @staticmethod
    def select_story_to_tell(agent: Agent, listener_id: str) -> Optional[Dict[str, Any]]:
        """
        Phase 17: Picks a story to share.
        Ideally disjoint from what we think listener knows, but for now random/recent.
        """
        if not agent.stories:
            return None
        return agent.stories[-1] # Share most recent for now
