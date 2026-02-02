from src.agent_planner import AgentPlanner
from src.entity import Agent
from src.physics import ActionType

def test():
    agent = Agent(name="UseTheMap", location_id="A", energy=50)
    agent.cognitive_map = {
        "A": {"neighbors": ["B"]},
        "B": {"neighbors": ["A", "C"]},
        "C": {"neighbors": ["B", "D"]},
        "D": {"neighbors": ["C", "E"]},
        "E": {"neighbors": ["D"], "objects": ["FOOD"]}
    }
    
    print("Testing Planner...")
    plan = AgentPlanner.generate_plan(agent)
    print(f"Plan Result: {plan}")
    if plan:
        print(f"Plan Steps: {[a.target_id for a in plan]}")
    else:
        print("Plan is empty.")

if __name__ == "__main__":
    test()
