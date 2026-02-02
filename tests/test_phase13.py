import unittest
from src.entity import Agent, Object, ObjectType
from src.world import World
from src.physics import Physics, Action, ActionType
from src.sim import Simulation
from src.agent_mind import AgentMind
from src.agent_meta import AgentMeta

class TestPhase13(unittest.TestCase):
    def test_hazard_damage(self):
        """Verify hazards cause energy loss."""
        world = World()
        world.add_location("FireRoom", [])
        hazard = Object(type=ObjectType.HAZARD, value=10, location_id="FireRoom")
        world.add_entity(hazard)
        
        agent = Agent(name="Tester", location_id="FireRoom", energy=100)
        
        # apply tick metabolism (Metabolism 1 + Hazard 10 = 11)
        effect = Physics.apply_tick_metabolism(world, agent)
        self.assertEqual(effect.energy_cost, 11)

    def test_alarm_avoidance(self):
        """Verify that an alarm call causes others to avoid the room."""
        sim = Simulation(seed=1)
        sim.world.add_location("A", ["Danger"])
        sim.world.add_location("Danger", ["A"])
        sim.world.add_location("Safe", ["A"])
        
        # Agent A is at Danger, sees hazard
        hazard = Object(type=ObjectType.HAZARD, value=10, location_id="Danger")
        sim.world.add_entity(hazard)
        
        agent_a = Agent(name="Witness", location_id="Danger", energy=100)
        sim.world.add_entity(agent_a)
        
        # Agent B is at A
        agent_b = Agent(name="Socialite", location_id="A", energy=100)
        agent_b.trust_scores[agent_a.id] = 1.0 # High trust
        sim.world.add_entity(agent_b)
        
        # 1. Agent A perceives and decides (Reflex: ALARM)
        # We'll run Tick 0. To ensure B doesn't move randomly to Danger in T0,
        # we can give it a WAIT plan or just let it happen and check T1.
        # Actually, let's give B a plan to WAIT in T0.
        agent_b.plan_queue = [Action(ActionType.WAIT)]
        
        sim.tick() # Tick 0: A screams, B waits at A.
        print(f"B loc after T0: {agent_b.location_id}")
        
        sim.tick() # Tick 1: B processes Alarm, updates reflection, decides.
        print(f"B loc after T1: {agent_b.location_id}")
        
        # B's reflection score for "Danger" should be negative
        score = AgentMeta.get_score(agent_b, "Danger")
        print(f"B Score for Danger: {score}")
        self.assertLess(score, 0)
        
        # B should NOT move to Danger in T1
        self.assertNotEqual(agent_b.location_id, "Danger")

if __name__ == '__main__':
    unittest.main()
