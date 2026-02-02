import unittest
import os
from src.sim import Simulation
from src.entity import Agent, Object, ObjectType
from src.agent_planner import AgentPlanner
from src.physics import ActionType

class TestPhase5(unittest.TestCase):
    def setUp(self):
        self.log_file = "test_phase5.jsonl"
        self.sim = Simulation(log_path=self.log_file, seed=123)
        
        # Build Map: A -> B -> C (Food)
        self.sim.world.add_location("A", ["B"])
        self.sim.world.add_location("B", ["A", "C"])
        self.sim.world.add_location("C", ["B"])
        
        self.food = Object(ObjectType.FOOD, 10, "C")
        self.sim.world.add_entity(self.food)
        
    def tearDown(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
            
    def test_planner_pathfinding(self):
        """Verify planner finds path to known food."""
        agent = Agent(location_id="A")
        
        # Inject Knowledge so Planner works
        agent.cognitive_map = {
            "A": {"neighbors": ["B"]},
            "B": {"neighbors": ["A", "C"]},
            "C": {"neighbors": ["B"], "objects": ["FOOD"]}
        }
        
        plan = AgentPlanner.generate_plan(agent)
        
        self.assertEqual(len(plan), 2, "Path A->B->C should be 2 moves")
        self.assertEqual(plan[0].type, ActionType.MOVE)
        self.assertEqual(plan[0].target_id, "B")
        self.assertEqual(plan[1].target_id, "C")

    def test_sim_plan_execution(self):
        """Verify agent follows the plan in simulation."""
        agent = Agent(location_id="A")
        # Pre-load map so it knows where food is
        agent.cognitive_map = {
            "A": {"neighbors": ["B"]},
            "B": {"neighbors": ["A", "C"]},
            "C": {"neighbors": ["B"], "objects": ["FOOD"]}
        }
        self.sim.world.add_entity(agent)
        
        # Run 3 ticks: Move B, Move C, Consume
        self.sim.run(max_ticks=3)
        
        # Check final state
        self.assertEqual(agent.location_id, "C")
        # Verify consumed (Energy > default 100 - costs + food)
        # Wait, Sim energy logic: default? Agent(energy=100). Cost Move=5. Food=10.
        # Tick 1: Move B (-5) = 95
        # Tick 2: Move C (-5) = 90
        # Tick 3: Consume (+10) = 100
        # Wait, Consume logic: If food value 10.
        # Check if food removed?
        current_food = [o for o in self.sim.world.entities.values() if isinstance(o, Object) and o.type == ObjectType.FOOD]
        self.assertEqual(len(current_food), 0, "Food should be consumed")

if __name__ == '__main__':
    unittest.main()
