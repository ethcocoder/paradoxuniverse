import unittest
from src.entity import Agent
from src.physics import ActionType
from src.agent_memory_pro import MemoryAnalyzer
from src.agent_planner import AgentPlanner

class TestPhase8(unittest.TestCase):
    def test_pattern_learning(self):
        """Verify that MemoryAnalyzer learns from perceptions."""
        agent = Agent(name="Learner", location_id="A")
        
        # 1. Visit B and see NO food (visits=1, hits=0)
        perception_bad = {"location": "B", "visible_food": []}
        MemoryAnalyzer.update_patterns(agent, perception_bad)
        
        # 2. Visit C and see food (visits=1, hits=1)
        perception_good = {"location": "C", "visible_food": ["f1"]}
        MemoryAnalyzer.update_patterns(agent, perception_good)
        
        self.assertEqual(agent.spatial_patterns["B"]["food_hits"], 0)
        self.assertEqual(agent.spatial_patterns["C"]["food_hits"], 1)
        
        # Predict
        best = MemoryAnalyzer.predict_resource_location(agent)
        self.assertEqual(best, "C")

    def test_planner_prediction(self):
        """Verify planner targets historically rich room when no food is currently visible."""
        agent = Agent(name="Predicter", location_id="A")
        # Knowledge of neighbors but NO food in cognitive_map
        agent.cognitive_map = {
            "A": {"neighbors": ["B", "C"]},
            "B": {"neighbors": ["A"]},
            "C": {"neighbors": ["A"]}
        }
        
        # Set history: C is 100% food room, B is 0%
        agent.spatial_patterns = {
            "B": {"visits": 10.0, "food_hits": 0.0},
            "C": {"visits": 10.0, "food_hits": 10.0}
        }
        
        # Generate plan. It should target C.
        plan = AgentPlanner.generate_plan(agent)
        
        self.assertTrue(len(plan) > 0)
        self.assertEqual(plan[0].target_id, "C")

if __name__ == '__main__':
    unittest.main()
