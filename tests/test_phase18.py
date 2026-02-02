import unittest
from src.entity import Agent, Object, ObjectType
from src.world import World
from src.physics import Physics, Action, ActionType
from src.sim import Simulation
from src.agent_planner import AgentPlanner
from src.agent_goals import GoalType, GoalManager

class TestPhase18(unittest.TestCase):
    def test_probabilistic_planning(self):
        """Verify agent plans to go to a high-probability food location even if not currently visible."""
        # Setup Agent with Map but no visible food
        agent = Agent(name="Hunter", location_id="Start", energy=50) # Hungry
        
        # Map: Start <-> Hall <-> Kitchen
        agent.cognitive_map = {
            "Start": {"neighbors": ["Hall"], "objects": []},
            "Hall": {"neighbors": ["Start", "Kitchen"], "objects": []},
            "Kitchen": {"neighbors": ["Hall"], "objects": []} # Currently empty in map!
        }
        
        # Inject Long-term Memory: Kitchen is good!
        agent.spatial_patterns = {
            "Kitchen": {"food_hits": 5, "total_visits": 5} # 100% success rate
        }
        
        # Generate Plan
        # GoalManager should select SURVIVAL because energy=50
        # AgentPlanner should select Kitchen (Score 75) over Hall/Start (Score 50 or 0)
        
        plan = AgentPlanner.generate_plan(agent)
        
        self.assertTrue(len(plan) > 0)
        # Expected path: Start -> Hall -> Kitchen. Length 2.
        # Action 0: Move Hall. Action 1: Move Kitchen.
        self.assertEqual(plan[0].type, ActionType.MOVE)
        self.assertEqual(plan[0].target_id, "Hall")
        self.assertEqual(plan[-1].target_id, "Kitchen")

if __name__ == '__main__':
    unittest.main()
