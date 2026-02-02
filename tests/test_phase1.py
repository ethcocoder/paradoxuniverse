import unittest
import os
from src.sim import Simulation
from src.entity import Agent, Object, ObjectType
from src.physics import Action, ActionType, Physics

class TestPhase1(unittest.TestCase):
    def setUp(self):
        self.log_file = "test_run.jsonl"
        self.sim = Simulation(log_path=self.log_file, seed=42)
        
        # Setup simple world
        self.sim.world.add_location("A", ["B"])
        self.sim.world.add_location("B", ["A"])
        
        # Food in B
        self.food = Object(type=ObjectType.FOOD, value=10, location_id="B")
        self.sim.world.add_entity(self.food)
        
        # Agent in A
        self.agent = Agent(name="Tester", location_id="A", energy=20)
        self.sim.world.add_entity(self.agent)

    def tearDown(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def test_movement_cost(self):
        """Verify moving costs energy."""
        start_energy = self.agent.energy
        
        # Force move action
        def controller(agent, world):
            return Action(ActionType.MOVE, target_id="B")
            
        self.sim.tick(controller)
        
        expected_cost = Physics.METABOLISM_COST + Physics.MOVE_COST
        self.assertEqual(self.agent.energy, start_energy - expected_cost)
        self.assertEqual(self.agent.location_id, "B")

    def test_consume_mechanics(self):
        """Verify eating adds energy and removes object."""
        # Teleport agent to B for test setup
        self.agent.location_id = "B"
        start_energy = self.agent.energy
        
        def controller(agent, world):
            return Action(ActionType.CONSUME, target_id=self.food.id)
            
        self.sim.tick(controller)
        
        expected_change = self.food.value - Physics.METABOLISM_COST
        self.assertEqual(self.agent.energy, start_energy + expected_change)
        
        # Food should be gone
        objects_in_b = self.sim.world.get_objects_at("B")
        self.assertNotIn(self.food, objects_in_b)

    def test_determinism(self):
        """Verify that two runs with same seed produce identical states if inputs are identical."""
        # For this to work, we need a deterministic controller or sequence of actions
        
        def run_scenario():
            s = Simulation(log_path="det_test.jsonl", seed=555)
            s.world.add_location("X", ["Y"])
            s.world.add_location("Y", ["X"])
            a = Agent(location_id="X", energy=100)
            s.world.add_entity(a)
            
            # Tick 1: Random (seeded)
            s.tick() 
            e1 = a.energy
            l1 = a.location_id
            
            # Tick 2: Random (seeded)
            s.tick()
            e2 = a.energy
            l2 = a.location_id
            return e1, l1, e2, l2
            
        r1 = run_scenario()
        r2 = run_scenario()
        
        self.assertEqual(r1, r2)
        if os.path.exists("det_test.jsonl"):
            os.remove("det_test.jsonl")

if __name__ == '__main__':
    unittest.main()
