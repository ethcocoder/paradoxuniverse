import unittest
from src.entity import Agent, Object, ObjectType
from src.world import World
from src.physics import Physics, Action, ActionType
from src.sim import Simulation
from src.agent_planner import AgentPlanner
from src.agent_mind import AgentMind

class TestPhase20(unittest.TestCase):
    def test_tool_use_planning(self):
        """Verify agent plans to get a tool to solve an obstacle."""
        agent = Agent(name="Locksmith", location_id="A", energy=100)
        
        # Room A <-> Room B <-> Room C
        # Key in B, Chest in C
        agent.cognitive_map = {
            "A": {"neighbors": ["B"], "objects": [], "last_tick": 0},
            "B": {
                "neighbors": ["A", "C"], 
                "objects": ["TOOL"], 
                "metadata": {"tools": [{"id": "Key1", "tool_type": "KEY"}]},
                "last_tick": 0
            },
            "C": {
                "neighbors": ["B"], 
                "objects": ["OBSTACLE"], 
                "metadata": {"obstacles": [{"id": "Chest1", "tool_required": "KEY"}]},
                "last_tick": 0
            }
        }
        
        # Generate Plan
        plan = AgentPlanner.generate_plan(agent)
        
        # Planner should target Room B first to get the key
        self.assertTrue(len(plan) > 0)
        self.assertEqual(plan[0].target_id, "B")
        
    def test_physics_use_rule(self):
        """Verify the USE action works only with the correct tool."""
        world = World()
        agent = Agent(id="Agent1", location_id="Room1")
        key = Object(id="Key1", type=ObjectType.TOOL, tool_type="KEY")
        chest = Object(id="Chest1", type=ObjectType.OBSTACLE, tool_required="KEY", location_id="Room1")
        
        world.add_entity(agent)
        world.add_entity(chest)
        
        # Try USE without key
        action = Action(ActionType.USE, target_id="Chest1")
        effect = Physics.apply_action(world, agent, action)
        self.assertFalse(effect.success)
        self.assertIn("Need a KEY", effect.message)
        
        # Give agent the key
        agent.inventory.append(key)
        effect = Physics.apply_action(world, agent, action)
        self.assertTrue(effect.success)
        self.assertEqual(effect.removed_object_id, "Chest1")

if __name__ == '__main__':
    unittest.main()
