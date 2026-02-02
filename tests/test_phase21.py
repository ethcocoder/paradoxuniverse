import unittest
from src.entity import Agent, Object, ObjectType
from src.world import World
from src.physics import Physics, Action, ActionType
from src.sim import Simulation

class TestPhase21(unittest.TestCase):
    def test_multi_agent_use_rule(self):
        """Verify the USE action requires enough agents."""
        world = World()
        agent1 = Agent(id="Agent1", location_id="GateRoom")
        agent2 = Agent(id="Agent2", location_id="GateRoom")
        lever = Object(id="Lever1", type=ObjectType.OBSTACLE, required_agents=2, location_id="GateRoom")
        
        world.add_entity(agent1)
        world.add_entity(lever)
        
        # 1. Try USE with only 1 agent
        action = Action(ActionType.USE, target_id="Lever1")
        effect = Physics.apply_action(world, agent1, action)
        self.assertFalse(effect.success)
        self.assertIn("Need 2 agents", effect.message)
        
        # 2. Add second agent
        world.add_entity(agent2)
        effect = Physics.apply_action(world, agent1, action)
        self.assertTrue(effect.success)
        self.assertEqual(effect.removed_object_id, "Lever1")
        
    def test_puzzle_help_broadcast(self):
        """Verify that an agent calls for help when at a multi-agent puzzle."""
        sim = Simulation(seed=100)
        sim.world.add_location("GateRoom", [])
        agent = Agent(id="Worker", location_id="GateRoom", energy=100)
        lever = Object(id="HeavyLever", type=ObjectType.OBSTACLE, required_agents=2, location_id="GateRoom")
        
        sim.world.add_entity(agent)
        sim.world.add_entity(lever)
        
        # Perception and Decision
        # Since it's at a puzzle needing 2 but only 1 there, it should COMMUNICATE
        sim.tick()
        
        # Check log file for PUZZLE_HELP_SENT
        import json
        with open(sim.logger.filepath, 'r') as f:
            logs = [json.loads(line) for line in f]
            
        help_calls = [log for log in logs if log["type"] == "PUZZLE_HELP_SENT"]
        if not help_calls:
            print("\nLOGS FOUND:")
            for l in logs: print(l)
        self.assertTrue(len(help_calls) > 0)
        self.assertEqual(help_calls[0]["puzzle"], "HeavyLever")

if __name__ == '__main__':
    unittest.main()
