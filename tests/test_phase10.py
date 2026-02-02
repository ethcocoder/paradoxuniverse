import unittest
from src.entity import Agent
from src.physics import Action, ActionType
from src.agent_mind import AgentMind

class TestPhase10(unittest.TestCase):
    def test_stay_at_home_survival(self):
        """Verify that agent waits instead of moving to a deathly node."""
        # Energy = 6. 
        # Metabolic cost = 1. Move cost = 5. Total = 6.
        # Energy after move = 0. Unsafe (6-6=0 < threshold 3.0)
        agent = Agent(name="Survivor", energy=6)
        
        perception = {
            "energy": 6,
            "location": "A",
            "visible_food": [],
            "neighbors": ["B"], # Neighbor exists but it's too far/expensive
            "visible_agents": []
        }
        
        # Decide fallback move
        action = AgentMind._choose_move(agent, perception)
        
        self.assertEqual(action.type, ActionType.WAIT, "Agent should WAIT to conserve energy if moving is suicidal.")

    def test_move_is_safe_with_buffer(self):
        """Verify that agent moves if it has enough energy buffer."""
        # Energy = 10. 
        # Move costs 6. Remaining 4. 4 > 3.0 (threshold). Safe.
        agent = Agent(name="Healthy", energy=10)
        
        perception = {
            "energy": 10,
            "location": "A",
            "visible_food": [],
            "neighbors": ["B"],
            "visible_agents": []
        }
        
        action = AgentMind._choose_move(agent, perception)
        
        self.assertEqual(action.type, ActionType.MOVE)
        self.assertEqual(action.target_id, "B")

if __name__ == '__main__':
    unittest.main()
