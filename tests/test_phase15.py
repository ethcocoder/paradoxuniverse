import unittest
from src.entity import Agent, Object, ObjectType
from src.world import World
from src.physics import Physics, Action, ActionType
from src.sim import Simulation
from src.agent_mind import AgentMind

class TestPhase15(unittest.TestCase):
    def test_coop_extraction_constraint(self):
        """Verify extract fails if not enough agents."""
        world = World()
        world.add_location("Cliff", [])
        # Large food requiring 2 agents
        obj = Object(id="Mammoth", type=ObjectType.COOP_FOOD, value=100, location_id="Cliff", required_agents=2)
        world.add_entity(obj)
        
        agent = Agent(name="Solo", location_id="Cliff", energy=100)
        world.add_entity(agent)
        
        # Action: Extract
        action = Action(ActionType.EXTRACT, target_id="Mammoth")
        effect = Physics.apply_action(world, agent, action)
        
        self.assertFalse(effect.success)
        self.assertIn("Need 2 agents", effect.message)

    def test_coop_extraction_success(self):
        """Verify extract succeeds if enough agents."""
        world = World()
        world.add_location("Cliff", [])
        obj = Object(id="Mammoth", type=ObjectType.COOP_FOOD, value=100, location_id="Cliff", required_agents=2)
        world.add_entity(obj)
        
        agent_a = Agent(name="Hunter1", location_id="Cliff", energy=100)
        agent_b = Agent(name="Hunter2", location_id="Cliff", energy=100)
        world.add_entity(agent_a)
        world.add_entity(agent_b)
        
        action = Action(ActionType.EXTRACT, target_id="Mammoth")
        effect = Physics.apply_action(world, agent_a, action)
        
        self.assertTrue(effect.success)
        self.assertEqual(effect.energy_gain, 100)

    def test_help_call_communication(self):
        """Verify that a help call informs others about the resource."""
        sim = Simulation(seed=1)
        sim.world.add_location("A", ["B"])
        sim.world.add_location("B", ["A"])
        
        # Agent A sees coop food at A
        obj = Object(id="Mammoth", type=ObjectType.COOP_FOOD, value=100, location_id="A", required_agents=2)
        sim.world.add_entity(obj)
        
        agent_a = Agent(name="Witness", location_id="A", energy=100)
        sim.world.add_entity(agent_a)
        
        # Agent B is at B
        agent_b = Agent(name="Socialite", location_id="B", energy=100)
        agent_b.trust_scores[agent_a.id] = 1.0 # High trust
        print(f"DEBUG: Map A ID: {id(agent_a.cognitive_map)}")
        print(f"DEBUG: Map B ID: {id(agent_b.cognitive_map)}")
        sim.world.add_entity(agent_b)
        
        # 1. Agent A decides (should be HELP_CALL)
        p_a = AgentMind.perceive(sim.world, agent_a)
        action_a = AgentMind.decide(agent_a, p_a)
        print(f"DEBUG: A Action: {action_a}")
        self.assertEqual(action_a.target_id, "HELP_CALL")
        
        # 2. Run simulation tick to deliver message
        sim.tick() # Tick 0: A sends call. If B is later in loop, B processes it.
        
        # B should now know about COOP_FOOD at A in its cognitive map
        # (Wait, if B is before A, B might need another tick. To be safe, let's check B's queue or tick again)
        if not agent_b.cognitive_map.get("A", {}).get("objects"):
             sim.tick() # Tick 1
             
        node_data = agent_b.cognitive_map.get("A", {})
        self.assertIn("COOP_FOOD", node_data.get("objects", []))

if __name__ == '__main__':
    unittest.main()
