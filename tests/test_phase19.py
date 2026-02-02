import unittest
from src.entity import Agent, Object, ObjectType
from src.world import World
from src.physics import Physics, Action, ActionType
from src.sim import Simulation
from src.agent_planner import AgentPlanner

class TestPhase19(unittest.TestCase):
    def test_stale_frontier_planning(self):
        """Verify agent plans to revisit old locations."""
        agent = Agent(name="Patroller", location_id="LocB", energy=100)
        agent.last_tick_updated = 60
        
        # Map: LocA <-> LocB <-> LocC
        agent.cognitive_map = {
            "LocA": {
                "neighbors": ["LocB"], 
                "objects": [],
                "last_tick": 0 # Very old (Delta 60 > 50)
            },
            "LocB": {
                "neighbors": ["LocA", "LocC"], 
                "objects": [],
                "last_tick": 60 # Current
            },
            "LocC": {
                "neighbors": ["LocB"], 
                "objects": [],
                "last_tick": 50 # Recent (Delta 10 < 50)
            }
        }
        
        plan = AgentPlanner.generate_plan(agent)
        
        self.assertTrue(len(plan) > 0)
        # Expected: Move to LocA
        self.assertEqual(plan[0].target_id, "LocA")
        # Ensure it didn't pick LocC
        for step in plan:
             self.assertNotEqual(step.target_id, "LocC")

if __name__ == '__main__':
    unittest.main()
