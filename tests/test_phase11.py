import unittest
from src.entity import Agent, Object, ObjectType
from src.sim import Simulation
from src.agent_social import AgentSocial
from src.agent_communication import AgentCommunication
from src.physics import Action, ActionType

class TestPhase11(unittest.TestCase):
    def test_targeted_food_sharing(self):
        """Verify that an agent identifies and shares food info with a needy neighbor."""
        sim = Simulation(seed=1)
        # Agent A (Rich, knows food)
        agent_a = Agent(name="Donor", energy=100)
        agent_a.cognitive_map = {"F": {"objects": ["FOOD"]}}
        
        # Agent B (Needy)
        agent_b = Agent(name="Recipient", energy=10)
        
        sim.world.add_entity(agent_a)
        sim.world.add_entity(agent_b)
        
        # A's perception of B
        perception = {
            "energy": 100,
            "visible_agents": [{"id": agent_b.id, "energy": 10}]
        }
        
        # A decides
        action = AgentSocial.decide_cooperation(agent_a, perception)
        
        self.assertIsNotNone(action)
        self.assertEqual(action.type, ActionType.COMMUNICATE)
        self.assertEqual(action.target_id, agent_b.id)
        
        # High value info check
        info = AgentSocial.identify_highest_value_info(agent_a)
        self.assertEqual(info["location_id"], "F")

    def test_trust_reward_for_food(self):
        """Verify trust boost when receiving food info."""
        agent_b = Agent(name="Recipient", energy=10)
        agent_b.trust_scores["Donor"] = 0.5
        
        # Received message with food info
        msg = {
            "sender_id": "Donor",
            "payload": {"F": {"objects": ["FOOD"]}}
        }
        agent_b.message_queue.append(msg)
        
        # Process
        AgentCommunication.process_messages(agent_b)
        
        # Initial 0.5 + 0.05 (msg) + 0.15 (food discovery) = 0.7
        self.assertAlmostEqual(agent_b.trust_scores["Donor"], 0.7)

if __name__ == '__main__':
    unittest.main()
