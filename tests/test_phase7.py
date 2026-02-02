import unittest
import os
from src.sim import Simulation
from src.entity import Agent, Object, ObjectType
from src.agent_goals import GoalManager, GoalType
from src.agent_mind import AgentMind

class TestPhase7(unittest.TestCase):
    def setUp(self):
        self.log_file = "test_phase7.jsonl"
        self.sim = Simulation(log_path=self.log_file, seed=123)
        self.sim.world.add_location("A", ["B"])
        
    def tearDown(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
            
    def test_goal_selection_survival(self):
        """Verify low energy triggers survival goal."""
        agent = Agent(name="Hungry", location_id="A", energy=20)
        perception = {"energy": 20, "visible_agents": []}
        
        goal = GoalManager.select_top_goal(agent, perception)
        self.assertEqual(goal.type, GoalType.SURVIVAL)
        
    def test_goal_selection_explore(self):
        """Verify high energy defaults to explore goal."""
        agent = Agent(name="Full", location_id="A", energy=100)
        perception = {"energy": 100, "visible_agents": []}
        
        goal = GoalManager.select_top_goal(agent, perception)
        self.assertEqual(goal.type, GoalType.EXPLORE)

    def test_goal_switching_clears_plan(self):
        """Verify that switching goals clears the old plan queue."""
        agent = Agent(name="Transition", location_id="A", energy=100)
        agent.plan_queue = ["dummy_action"]
        agent.current_goal = "EXPLORE"
        
        # Perception showing critical hunger
        perception = AgentMind.perceive(self.sim.world, agent)
        agent.energy = 10 # Force hunger AFTER perception for the test or use modified perception
        perception["energy"] = 10
        
        # Decide should trigger GoalManager -> Goal Switch -> Clear Queue
        AgentMind.decide(agent, perception)
        
        self.assertEqual(agent.current_goal, "SURVIVAL")
        self.assertEqual(len(agent.plan_queue), 0, "Plan queue should be cleared on goal switch")

if __name__ == '__main__':
    unittest.main()
