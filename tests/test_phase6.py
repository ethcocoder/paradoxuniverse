import unittest
import os
from src.sim import Simulation
from src.entity import Agent, Object, ObjectType
from src.agent_social import AgentSocial
from src.agent_mind import AgentMind
from src.physics import ActionType

class TestPhase6(unittest.TestCase):
    def setUp(self):
        self.log_file = "test_phase6.jsonl"
        self.sim = Simulation(log_path=self.log_file, seed=123)
        self.sim.world.add_location("Room_A", [])
        
    def tearDown(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
            
    def test_social_perception(self):
        """Verify agents see each other and update social map."""
        a1 = Agent(name="Observer", location_id="Room_A")
        a2 = Agent(name="Target", location_id="Room_A", energy=50)
        self.sim.world.add_entity(a1)
        self.sim.world.add_entity(a2)
        
        # Run perception manually
        p = AgentMind.perceive(self.sim.world, a1)
        
        # Check visible agents
        self.assertEqual(len(p["visible_agents"]), 1)
        self.assertEqual(p["visible_agents"][0]["id"], a2.id)
        
        # Check Social Map Update
        self.assertIn(a2.id, a1.social_map)
        self.assertEqual(a1.social_map[a2.id]["energy"], 50)
        self.assertIn(a2.id, a1.trust_scores) 
        self.assertEqual(a1.trust_scores[a2.id], AgentSocial.INITIAL_TRUST)
        
    def test_altruism_decision(self):
        """Verify Rich Agent helps Poor Neighbor."""
        rich = Agent(name="Rich", location_id="Room_A", energy=90)
        poor = Agent(name="Poor", location_id="Room_A", energy=20)
        
        self.sim.world.add_entity(rich)
        self.sim.world.add_entity(poor)
        
        # Force Perception
        perception = AgentMind.perceive(self.sim.world, rich)
        
        # Decide
        action = AgentMind.decide(rich, perception)
        
        # Expectation: COMMUNICATE (Sharing Info)
        self.assertEqual(action.type, ActionType.COMMUNICATE)
        self.assertEqual(action.target_id, poor.id)

if __name__ == '__main__':
    unittest.main()
