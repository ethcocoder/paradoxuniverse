import unittest
import os
from src.sim import Simulation
from src.entity import Agent, Object, ObjectType
from src.agent_mind import AgentMind
from src.physics import Physics

class TestPhase2(unittest.TestCase):
    def setUp(self):
        self.log_file = "test_phase2.jsonl"
        self.sim = Simulation(log_path=self.log_file, seed=101)
        
        # Setup world: A <-> B
        self.sim.world.add_location("A", ["B"])
        self.sim.world.add_location("B", ["A"])
        
    def tearDown(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def test_perception_and_memory(self):
        """Verify agent perceives world and stores it in memory."""
        agent = Agent(location_id="A", energy=100)
        self.sim.world.add_entity(agent)
        
        # Run 1 tick
        self.sim.tick()
        
        # Check Memory
        self.assertEqual(len(agent.memory), 1)
        last_mem = agent.memory[0]
        self.assertEqual(last_mem["location"], "A")
        self.assertEqual(last_mem["energy"], 100 - Physics.METABOLISM_COST)
        self.assertEqual(last_mem["neighbors"], ["B"])

    def test_survival_instinct(self):
        """Verify agent eats when hungry."""
        # Low energy agent in room with food
        agent = Agent(location_id="A", energy=AgentMind.SURVIVAL_THRESHOLD - 5)
        self.sim.world.add_entity(agent)
        
        food = Object(type=ObjectType.FOOD, value=50, location_id="A")
        self.sim.world.add_entity(food)
        
        # Tick should trigger perception -> decide(EAT) -> act
        self.sim.tick()
        
        # Agent should have gained energy (start + food - metabolism)
        expected_energy = (AgentMind.SURVIVAL_THRESHOLD - 5) + 50 - Physics.METABOLISM_COST
        self.assertEqual(agent.energy, expected_energy)
        
        # Food should be gone
        self.assertEqual(len(self.sim.world.get_objects_at("A")), 0)

    def test_boredom_mechanism(self):
        """Verify agent moves if stuck in same place."""
        agent = Agent(location_id="A", energy=100)
        self.sim.world.add_entity(agent)
        
        # Force stay for BOREDOM_MAX ticks
        # We can simulate this by manually filling memory or just running loop
        # Since logic decides to move if memory shows same location, let's run N ticks
        # It might move randomly before max, but at Max it MUST move if possible.
        
        # Let's seed simulation to ensure it doesn't random move early?
        # Actually proper test: Fill memory with "A", check if decision is MOVE
        
        agent.memory = [{"location": "A"}] * AgentMind.BOREDOM_MAX
        perception = AgentMind.perceive(self.sim.world, agent) # Get fresh perception
        
        action = AgentMind.decide(agent, perception)
        
        # Should be MOVE because bored
        self.assertEqual(action.type.name, "MOVE")

    def test_visited_tracking(self):
        """Verify visited locations are tracked."""
        agent = Agent(location_id="A", energy=100)
        self.sim.world.add_entity(agent)
        
        self.sim.tick() # Perceived A
        self.assertIn("A", agent.visited_locations)
        
        # Force move to B
        self.sim.world.move_agent(agent.id, "B")
        self.sim.tick() # Perceived B
        
        self.assertIn("B", agent.visited_locations)
        self.assertEqual(len(agent.visited_locations), 2)

if __name__ == '__main__':
    unittest.main()
