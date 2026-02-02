import unittest
from src.entity import Agent, Object, ObjectType
from src.world import World
from src.physics import Physics, Action, ActionType
from src.sim import Simulation
from src.agent_mind import AgentMind
from src.agent_social import AgentSocial
from src.agent_meta import AgentMeta

class TestPhase17(unittest.TestCase):
    def test_story_generation(self):
        """Verify agent generates a story upon seeing a hazard."""
        sim = Simulation(seed=1)
        sim.world.add_location("DangerRoom", [])
        
        # Hazard
        haz = Object(id="Spike", type=ObjectType.HAZARD, value=10, location_id="DangerRoom")
        sim.world.add_entity(haz)
        
        agent = Agent(name="Witness", location_id="DangerRoom", energy=100)
        sim.world.add_entity(agent)
        
        # Perception Trigger
        # Run perceive
        p = AgentMind.perceive(sim.world, agent)
        # Run decide (which triggers generate_story)
        AgentMind.decide(agent, p)
        
        self.assertEqual(len(agent.stories), 1)
        self.assertEqual(agent.stories[0]["topic"], "HAZARD")
        self.assertEqual(agent.stories[0]["location"], "DangerRoom")

    def test_story_propagation_and_avoidance(self):
        """Verify Agent B learns about hazard from A and avoids it."""
        sim = Simulation(seed=42)
        sim.world.add_location("SafeRoom", ["DangerRoom"])
        sim.world.add_location("DangerRoom", ["SafeRoom"])
        
        # Hazard at DangerRoom
        haz = Object(id="Spike", type=ObjectType.HAZARD, value=10, location_id="DangerRoom")
        sim.world.add_entity(haz)
        
        # Agents interact at SafeRoom
        agent_a = Agent(name="Storyteller", location_id="SafeRoom", energy=100)
        # Pre-seed A with the story (as if they saw it)
        agent_a.stories.append({
             "topic": "HAZARD",
             "location": "DangerRoom",
             "tick": 0,
             "source": agent_a.id,
             "veracity": 1.0
        })
        
        agent_b = Agent(name="Listener", location_id="SafeRoom", energy=100)
        agent_b.trust_scores[agent_a.id] = 1.0 # High trust
        
        sim.world.add_entity(agent_a)
        sim.world.add_entity(agent_b)
        
        # T0: A decides to gossip (goal SOCIAL)
        agent_a.current_goal = "SOCIAL" 
        # But we need to make sure A *actually* gossips.
        # AgentMind.decide checks active_goal.
        # B just waits.
        
        # Let's force A to decide GOSSIP
        p_a = AgentMind.perceive(sim.world, agent_a)
        p_a["visible_agents"] = [{"id": agent_b.id, "distance": 0}] # Fake proximity for test logic simplicity if needed
        # decide() calls AgentSocial which checks distance 0 agents.
        # Real sim perceive should handle this, provided update_social_map runs or we use simple list.
        # In AgentMind.perceive, visible_agents is populated.
        
        sim.tick() # T0
        
        # Check if B received story
        # B processes messages at START of T1
        sim.tick() # T1
        
        # Verify B took the warning
        score = AgentMeta.get_score(agent_b, "DangerRoom")
        print(f"DEBUG: B's score for DangerRoom: {score}")
        self.assertLess(score, 0.0) # Should be negative (penalty)
        
        # Verify B has 'HAZARD' in cognitive map
        node_b = agent_b.cognitive_map.get("DangerRoom", {})
        self.assertIn("HAZARD", node_b.get("objects", []))

if __name__ == '__main__':
    unittest.main()
