from src.sim import Simulation
from src.entity import Agent, Object, ObjectType
from src.physics import Action, ActionType, Physics

def main():
    # 1. Init Simulation
    sim = Simulation(log_path="phase20_run.jsonl", seed=80)
    
    # 2. Build World
    sim.world.add_location("Entrance", ["Guardroom"])
    sim.world.add_location("Guardroom", ["Entrance", "Vault"])
    sim.world.add_location("Vault", ["Guardroom"])
    
    # Add Key
    key = Object(id="Key", type=ObjectType.TOOL, tool_type="KEY", location_id="Guardroom")
    sim.world.add_entity(key)
    
    # Add Chest
    chest = Object(id="TreasureChest", type=ObjectType.OBSTACLE, tool_required="KEY", location_id="Vault")
    sim.world.add_entity(chest)
    
    # 3. Add Agent
    agent = Agent(name="Locksmith", location_id="Entrance", energy=100)
    
    # Pre-seed Map so agent knows where things are
    agent.cognitive_map = {
        "Entrance": {"neighbors": ["Guardroom"], "objects": [], "last_tick": 0},
        "Guardroom": {
            "neighbors": ["Entrance", "Vault"], 
            "objects": ["TOOL"], 
            "metadata": {"tools": [{"id": "Key", "tool_type": "KEY"}]},
            "last_tick": 0
        },
        "Vault": {
            "neighbors": ["Guardroom"], 
            "objects": ["OBSTACLE"], 
            "metadata": {"obstacles": [{"id": "TreasureChest", "tool_required": "KEY"}]},
            "last_tick": 0
        }
    }
    
    sim.world.add_entity(agent)
    
    # 4. Run
    print("Starting Phase 20 Verification Run (The Locksmith)...")
    
    # Tick 0: At Entrance. Plan: [Move Guardroom, Move Vault]
    # Tick 1: At Guardroom. Sees Key. PICKUP Key. Plan cleared.
    # Tick 2: At Guardroom. Plan: [Move Vault]
    # Tick 3: At Vault. Sees Chest+Have Key. USE Key.
    
    sim.run(max_ticks=8, agent_controller=None) 
    print("Run complete. Check phase20_run.jsonl")

if __name__ == "__main__":
    main()
