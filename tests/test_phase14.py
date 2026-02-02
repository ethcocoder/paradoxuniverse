import unittest
from src.entity import Agent, Object, ObjectType
from src.world import World
from src.physics import Physics, Action, ActionType
from src.sim import Simulation
from src.agent_mind import AgentMind

class TestPhase14(unittest.TestCase):
    def test_imitation_logic(self):
        """Verify that B follows A if trusted."""
        sim = Simulation(seed=42)
        sim.world.add_location("Home", ["West"])
        sim.world.add_location("West", ["Home"])
        
        agent_a = Agent(name="Leader", location_id="West", energy=100)
        sim.world.add_entity(agent_a)
        
        agent_b = Agent(name="Follower", location_id="Home", energy=100)
        agent_b.trust_scores[agent_a.id] = 1.0 # High trust
        sim.world.add_entity(agent_b)
        
        # 1. Perception Step
        # B should see A in the adjacent room "West"
        p_b = AgentMind.perceive(sim.world, agent_b)
        self.assertEqual(len(p_b["visible_agents"]), 1)
        self.assertEqual(p_b["visible_agents"][0]["location"], "West")
        
        # 2. Decision Step
        # B's goal should be SOCIAL (due to trusted leader nearby)
        # B's action should be MOVE to West (Imitation)
        action_b = AgentMind.decide(agent_b, p_b)
        self.assertEqual(action_b.type, ActionType.MOVE)
        self.assertEqual(action_b.target_id, "West")

    def test_trust_gating_imitation(self):
        """Verify that B does NOT follow A if trust is low."""
        sim = Simulation(seed=42)
        sim.world.add_location("Home", ["West", "East", "North", "South"])
        sim.world.add_location("West", ["Home"])
        sim.world.add_location("East", ["Home"])
        sim.world.add_location("North", ["Home"])
        sim.world.add_location("South", ["Home"])
        
        agent_a = Agent(name="Stranger", location_id="West", energy=100)
        sim.world.add_entity(agent_a)
        
        agent_b = Agent(name="Skeptic", location_id="Home", energy=100)
        agent_b.trust_scores[agent_a.id] = 0.1 # Low trust
        sim.world.add_entity(agent_b)
        
        p_b = AgentMind.perceive(sim.world, agent_b)
        action_b = AgentMind.decide(agent_b, p_b)
        
        # Should NOT be SOCIAL goal.
        self.assertNotEqual(agent_b.current_goal, "SOCIAL")
        # And if it's not SOCIAL, it's not imitation logic.
        # (It might still randomly move to West, but less likely.
        # To be 100% sure, we can check that AgentSocial.get_observation_to_imitate returns None)
        from src.agent_social import AgentSocial
        self.assertIsNone(AgentSocial.get_observation_to_imitate(agent_b, p_b))
if __name__ == '__main__':
    unittest.main()
