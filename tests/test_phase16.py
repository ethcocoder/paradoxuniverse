import unittest
from src.entity import Agent, Object, ObjectType
from src.world import World
from src.physics import Physics, Action, ActionType
from src.sim import Simulation
from src.agent_mind import AgentMind
from src.agent_social import AgentSocial

class TestPhase16(unittest.TestCase):
    def test_reputation_gain(self):
        """Verify reputation increases after helping with extraction."""
        sim = Simulation(seed=42)
        sim.world.add_location("Room", [])
        
        # 1. Setup Resource (Req=3 initially to delay extraction)
        res = Object(id="Res1", type=ObjectType.COOP_FOOD, value=50, location_id="Room", required_agents=3)
        sim.world.add_entity(res)
        
        # 2. Setup Agents
        agent_a = Agent(name="A", location_id="Room", energy=100)
        agent_b = Agent(name="B", location_id="Room", energy=100)
        sim.world.add_entity(agent_a)
        sim.world.add_entity(agent_b)
        
        # 3. Simulate Extraction
        # Tick 0: A & B perceive Res. Neither extracts (Req=3, Count=2).
        sim.tick() 
        
        # Change Requirement to 2
        res.required_agents = 2
        
        # Tick 1: A perceives Res (Req=2). A extracts.
        # B perceives Res (either before or after A).
        # If B before A: B sees Res.
        # If B after A: B sees No Res.
        # BUT B saw Res in T0. So "prev" (T0) has Res. "curr" (T1) has No Res.
        # This matches the trigger condition!
        sim.tick() 
        
        # Tick 2: B should have updated reputation
        sim.tick() 
        
        rep = agent_b.social_reputations.get(agent_a.id, 0.0)
        self.assertGreater(rep, 0.0)

    def test_reciprocity_bias(self):
        """Verify agent prioritizes helping those with better reputation."""
        sim = Simulation(seed=1)
        sim.world.add_location("Home", ["HelperLoc", "FreeRiderLoc"])
        sim.world.add_location("HelperLoc", ["Home"])
        sim.world.add_location("FreeRiderLoc", ["Home"])
        
        agent_b = Agent(name="B", location_id="Home", energy=100)
        
        # A is a helper (high reputation)
        agent_a_id = "agent_a"
        agent_b.social_reputations[agent_a_id] = 1.0
        agent_b.trust_scores[agent_a_id] = 1.0
        
        # C is a free-rider (low reputation)
        agent_c_id = "agent_c"
        agent_b.social_reputations[agent_c_id] = -1.0
        agent_b.trust_scores[agent_c_id] = 0.5 
        
        # Both send help calls for different locations
        # We manually inject this into B's map
        agent_b.cognitive_map["HelperLoc"] = {
            "neighbors": ["Home"],
            "objects": ["COOP_FOOD"],
            "requester_id": agent_a_id
        }
        agent_b.cognitive_map["FreeRiderLoc"] = {
            "neighbors": ["Home"],
            "objects": ["COOP_FOOD"],
            "requester_id": agent_c_id
        }
        
        sim.world.add_entity(agent_b)
        
        # B's decision should be to move toward HelperLoc
        p_b = AgentMind.perceive(sim.world, agent_b)
        action_b = AgentMind.decide(agent_b, p_b)
        
        self.assertEqual(action_b.type, ActionType.MOVE)
        self.assertEqual(action_b.target_id, "HelperLoc")

if __name__ == '__main__':
    unittest.main()
