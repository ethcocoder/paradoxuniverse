import unittest
from src.entity import Agent
from src.physics import Action, ActionType
from src.agent_imagination import ForwardModel
from src.agent_mind import AgentMind

class TestPhase9(unittest.TestCase):
    def test_forward_model_prediction(self):
        """Verify that ForwardModel correctly predicts starvation."""
        agent = Agent(name="Thinker", energy=10)
        # Plan: MOVE (Cost 5+1) -> MOVE (Cost 5+1) = 12 total.
        plan = [
            Action(ActionType.MOVE, target_id="B"),
            Action(ActionType.MOVE, target_id="C")
        ]
        
        results = ForwardModel.simulate_plan(agent, plan)
        for i, s in enumerate(results):
            print(f"Step {i}: {s}")
        
        # Initial State + 2 Actions
        self.assertEqual(len(results), 3)
        self.assertFalse(ForwardModel.is_plan_safe(agent, plan), "Plan should be marked unsafe")

    def test_mind_rejects_unsafe_plan(self):
        """Verify that AgentMind rejects a plan that would kill it."""
        agent = Agent(name="Tactician", energy=10)
        # Manually inject an unsafe plan
        agent.plan_queue = [
            Action(ActionType.MOVE, target_id="B"),
            Action(ActionType.MOVE, target_id="C")
        ]
        
        perception = {
            "energy": 10,
            "location": "A",
            "visible_food": [],
            "neighbors": ["B"],
            "visible_agents": []
        }
        
        # Decide should clear the queue because it's unsafe
        action = AgentMind.decide(agent, perception)
        
        self.assertEqual(len(agent.plan_queue), 0, "Mind should have aborted the suicidal plan")
        # In this specific scenario, even if it clears the plan, 
        # it might still move because of greedy fallback. 
        # To strictly test 'Imagination', we should verify the queue was cleared.

if __name__ == '__main__':
    unittest.main()
