from src.sim import Simulation
from src.entity import Agent, Object, ObjectType
from src.physics import Action, ActionType, Physics
from src.agent_planner import AgentPlanner

def main():
    # 1. Init Simulation
    sim = Simulation(log_path="phase18_run.jsonl", seed=60)
    
    # 2. Build World
    sim.world.add_location("Camp", ["Path"])
    sim.world.add_location("Path", ["Camp", "Forest"])
    sim.world.add_location("Forest", ["Path"]) 
    
    # 3. Add Agent (Hungry)
    agent = Agent(name="Hunter", location_id="Camp", energy=40)
    
    # Pre-seed Map (Agent knows the layout)
    agent.cognitive_map = {
        "Camp": {"neighbors": ["Path"], "objects": []},
        "Path": {"neighbors": ["Camp", "Forest"], "objects": []},
        "Forest": {"neighbors": ["Path"], "objects": []}
    }
    
    # Pre-seed Memory (Forest is good)
    agent.spatial_patterns = {
        "Forest": {"food_hits": 10, "total_visits": 10}, # 100%
        "Path": {"food_hits": 0, "total_visits": 5}
    }
    
    sim.world.add_entity(agent)
    
    # 4. Run
    print("Starting Phase 18 Verification Run (The Memory Hunter)...")
    
    # Tick 0: Agent is hungry. No visible food.
    # Planner should pick 'Forest' as LIKELY_REGION (Score 75).
    # Plan: Move Path -> Move Forest.
    
    sim.run(max_ticks=3, agent_controller=None) 
    print("Run complete. Check phase18_run.jsonl")

if __name__ == "__main__":
    main()
