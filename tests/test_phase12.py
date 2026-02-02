import unittest
from src.entity import Agent, Object, ObjectType
from src.world import World
from src.physics import Physics, Action, ActionType
from src.sim import Simulation
from src.agent_mind import AgentMind

class TestPhase12(unittest.TestCase):
    def test_pickup_and_drop_physics(self):
        """Verify that Physics correctly handles pickup and drop effects."""
        world = World()
        world.add_location("A", [])
        food = Object(id="f1", type=ObjectType.FOOD, location_id="A")
        world.add_entity(food)
        
        agent = Agent(name="Hoarder", location_id="A", energy=100)
        
        # Test Pickup
        action_pickup = Action(ActionType.PICKUP, target_id="f1")
        effect_pickup = Physics.apply_action(world, agent, action_pickup)
        self.assertTrue(effect_pickup.success)
        self.assertEqual(effect_pickup.removed_object_id, "f1")
        
        # Manually apply to agent for further testing
        agent.inventory.append(food)
        
        # Test Drop
        action_drop = Action(ActionType.DROP, target_id="f1")
        effect_drop = Physics.apply_action(world, agent, action_drop)
        self.assertTrue(effect_drop.success)
        self.assertEqual(effect_drop.added_object.id, "f1")

    def test_caching_simulation(self):
        """Verify that Simulation correctly transfers objects to/from inventory."""
        sim = Simulation(seed=1)
        sim.world.add_location("Home", [])
        food = Object(id="f1", type=ObjectType.FOOD, location_id="Home", value=50)
        sim.world.add_entity(food)
        
        agent = Agent(name="Squirrel", location_id="Home", energy=100)
        sim.world.add_entity(agent)
        
        # 1. Pickup
        action_pickup = Action(ActionType.PICKUP, target_id="f1")
        # Override decide for test
        effect = Physics.apply_action(sim.world, agent, action_pickup)
        sim._apply_effect(effect)
        
        self.assertEqual(len(agent.inventory), 1)
        self.assertEqual(agent.inventory[0].id, "f1")
        self.assertEqual(len(sim.world.get_objects_at("Home")), 0)
        
        # 2. Drop
        action_drop = Action(ActionType.DROP, target_id="f1")
        effect_drop = Physics.apply_action(sim.world, agent, action_drop)
        sim._apply_effect(effect_drop)
        
        self.assertEqual(len(agent.inventory), 0)
        self.assertEqual(len(sim.world.get_objects_at("Home")), 1)
        self.assertEqual(sim.world.get_objects_at("Home")[0].id, "f1")

    def test_mind_chooses_pickup(self):
        """Verify that AgentMind picks up food if energy is high."""
        agent = Agent(name="Hoarder", energy=90, location_id="A")
        # In EXPLORE goal, and at home. 
        agent.home_location_id = "A"
        
        perception = {
            "energy": 90,
            "location": "A",
            "visible_food": ["f1"],
            "neighbors": ["B"],
            "visible_agents": [],
            "inventory": []
        }
        
        action = AgentMind.decide(agent, perception)
        self.assertEqual(action.type, ActionType.PICKUP)

if __name__ == '__main__':
    unittest.main()
