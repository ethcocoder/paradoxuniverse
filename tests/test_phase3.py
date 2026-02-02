import unittest
import os
from src.sim import Simulation
from src.entity import Agent, Object, ObjectType
from src.agent_mind import AgentMind
from src.agent_communication import AgentCommunication
from src.physics import Action, ActionType

class TestPhase3(unittest.TestCase):
    def setUp(self):
        self.log_file = "test_phase3.jsonl"
        self.sim = Simulation(log_path=self.log_file, seed=202)
        
        # World: A <-> B (Hidden Room C connected to B)
        self.sim.world.add_location("A", ["B"])
        self.sim.world.add_location("B", ["A", "C"])
        self.sim.world.add_location("C", ["B"])
        
    def tearDown(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def test_communication_map_update(self):
        """Verify Agent A can tell Agent B about a location."""
        agent_a = Agent(name="A", location_id="B", energy=100) # Knows B, sees C
        agent_b = Agent(name="B", location_id="A", energy=100) # Knows A, sees B
        
        self.sim.world.add_entity(agent_a)
        self.sim.world.add_entity(agent_b)
        
        # 1. Agent A perceives B (and sees C is neighbor)
        # We manually force perception to ensure map is populated
        AgentMind.perceive(self.sim.world, agent_a)
        
        # Check A knows C exists (as neighbor of B)
        # Note: _update_map stores neighbors.
        # agent_a.cognitive_map["B"]["neighbors"] should contain "C"
        self.assertIn("C", agent_a.cognitive_map["B"]["neighbors"])
        
        # 2. Agent A broadcasts
        payload = agent_a.cognitive_map
        all_agents = [agent_a, agent_b] # Sim usually passes this
        AgentCommunication.broadcast(self.sim.world, agent_a, all_agents, payload)
        
        # 3. Agent B processes messages
        AgentCommunication.process_messages(agent_b)
        
        # 4. Agent B should now have data about B (including neighbor C)
        self.assertIn("B", agent_b.cognitive_map)
        self.assertIn("C", agent_b.cognitive_map["B"]["neighbors"])

    def test_food_location_sharing(self):
        """Verify Agent A shares food location, Agent B updates map."""
        agent_a = Agent(location_id="C", energy=100)
        agent_b = Agent(location_id="A", energy=100)
        
        self.sim.world.add_entity(agent_a)
        self.sim.world.add_entity(agent_b)
        
        # Put food in C
        food = Object(type=ObjectType.FOOD, location_id="C")
        self.sim.world.add_entity(food)
        
        # A Perceives
        AgentMind.perceive(self.sim.world, agent_a)
        # A knows C has Food
        self.assertIn("FOOD", agent_a.cognitive_map["C"]["objects"])
        
        # A Broadcasts
        AgentCommunication.broadcast(self.sim.world, agent_a, [agent_a, agent_b], agent_a.cognitive_map)
        
        # B Perceives (Process Msgs)
        AgentCommunication.process_messages(agent_b)
        
        # B should know C has Food
        self.assertIn("C", agent_b.cognitive_map)
        self.assertIn("FOOD", agent_b.cognitive_map["C"]["objects"])

if __name__ == '__main__':
    unittest.main()
