from src.sim import Simulation
from src.entity import Agent, Object, ObjectType
from src.physics import Action, ActionType, Physics
from src.agent_planner import AgentPlanner

def main():
    # 1. Init Simulation
    sim = Simulation(log_path="phase19_run.jsonl", seed=70)
    
    # 2. Build World
    sim.world.add_location("LocA", ["LocB"])
    sim.world.add_location("LocB", ["LocA", "LocC"])
    sim.world.add_location("LocC", ["LocB"])
    
    # 3. Add Agent
    agent = Agent(name="Patroller", location_id="LocB", energy=100)
    sim.world.add_entity(agent)
    
    # Pre-seed Map
    agent.cognitive_map = {
        "LocA": {"neighbors": ["LocB"], "objects": [], "last_tick": 0},
        "LocB": {"neighbors": ["LocA", "LocC"], "objects": [], "last_tick": 50},
        "LocC": {"neighbors": ["LocB"], "objects": [], "last_tick": 50}
    }
    
    # Manually advance time to make LocA stale
    sim.tick_count = 55
    agent.last_tick_updated = 55
    
    # 4. Run
    print("Starting Phase 19 Verification Run (The Patroller)...")
    
    # Tick 55: Agent is at LocB.
    # LocA is stale (diff 55 > 50).
    # LocC is fresh (diff 5).
    # Decision: Move LocA.
    
    sim.run(max_ticks=2, agent_controller=None) 
    print("Run complete. Check phase19_run.jsonl")

if __name__ == "__main__":
    main()
