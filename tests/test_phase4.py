import unittest
import os
from src.sim import Simulation
from src.entity import Agent
from src.agent_meta import AgentMeta
from src.agent_mind import AgentMind
from src.physics import Action, ActionType

class TestPhase4(unittest.TestCase):
    def setUp(self):
        self.log_file = "test_phase4.jsonl"
        self.sim = Simulation(log_path=self.log_file, seed=404)
        
        self.sim.world.add_location("A", ["B", "C"])
        self.sim.world.add_location("B", ["A"])
        self.sim.world.add_location("C", ["A"]) # Safe alternative
        
    def tearDown(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
            
    def test_reflection_penalty(self):
        """Verify repeated moves to same target incur penalty."""
        agent = Agent(location_id="A")
        
        # Manually inject history: 5 moves to "B"
        for _ in range(5):
            entry = {
                "tick": 0,
                "action": Action(ActionType.MOVE, target_id="B"),
                "success": True
            }
            agent.action_history.append(entry)
            
        AgentMeta.reflect(agent)
        
        score_b = AgentMeta.get_score(agent, "B")
        self.assertLess(score_b, 0.0, "B should have negative score due to repetition")
        
        score_c = AgentMeta.get_score(agent, "C")
        self.assertEqual(score_c, 0.0, "C should be neutral")

    def test_avoidance_heuristic(self):
        """Verify Mind avoids negatively scored locations."""
        agent = Agent(location_id="A")
        agent.visited_locations = {"A"} # so B and C are unvisited
        
        # Set B as "Bad"
        agent.reflection_score["B"] = -1.0
        
        perception = {
            "neighbors": ["B", "C"],
            # ... other fields irrelevant for _choose_move logic
        }
        
        # Run choice multiple times to ensure statistical avoidance or strict avoidance
        # Our logic is: filter safe first. B is unsafe (-1.0 < -0.5). C is safe (0).
        # So C must be chosen.
        
        for _ in range(10):
            action = AgentMind._choose_move(agent, perception)
            self.assertEqual(action.target_id, "C", "Should avoid B and pick C")

if __name__ == '__main__':
    unittest.main()
