from src.sim import Simulation
from src.entity import Agent, Object, ObjectType
from src.physics import Action, ActionType, Physics
from src.agent_meta import AgentMeta

def main():
    # 1. Init Simulation
    sim = Simulation(log_path="phase21_run.jsonl", seed=42)
    
    # 2. Build World
    sim.world.add_location("A", ["C"])
    sim.world.add_location("B", ["C"])
    sim.world.add_location("C", ["A", "B"])
    
    # Add Lever Tool
    lever_tool = Object(id="LeverTool", type=ObjectType.TOOL, tool_type="LEVER", location_id="A")
    sim.world.add_entity(lever_tool)
    
    # Add Heavy Gate
    gate = Object(id="HeavyGate", type=ObjectType.OBSTACLE, tool_required="LEVER", required_agents=2, location_id="C")
    sim.world.add_entity(gate)
    
    # 3. Add Agents
    # Agent 1: The Technician (knows about the gate and has the tool)
    a1 = Agent(name="Technician", location_id="A", energy=100)
    a1.cognitive_map = {
        "A": {"neighbors": ["C"], "objects": ["TOOL"], "metadata": {"tools": [{"id": "LeverTool", "tool_type": "LEVER"}]}, "last_tick": 0},
        "C": {"neighbors": ["A", "B"], "objects": ["OBSTACLE"], "metadata": {"obstacles": [{"id": "HeavyGate", "tool_required": "LEVER", "required_agents": 2}]}, "last_tick": 0}
    }
    
    # Agent 2: The Helper (nearby, but doesn't know about the gate)
    a2 = Agent(name="Helper", location_id="B", energy=100)
    a2.cognitive_map = {
        "B": {"neighbors": ["C"], "objects": [], "last_tick": 0},
        "C": {"neighbors": ["A", "B"], "objects": [], "last_tick": 0} # Knows room exists
    }
    
    sim.world.add_entity(a1)
    sim.world.add_entity(a2)
    
    # 4. Run
    print("Starting Phase 21 Verification Run (The Heavy Gate)...")
    
    # Expectation:
    # T0: A1 pickups Lever. A2 wanders/waits in B.
    # T1: A1 moves to C. A2 waits in B.
    # T2: A1 at C, sees Gate (needs 2). Broadcasts PUZZLE_HELP.
    # T3: A2 processes PUZZLE_HELP. Map updated. Moves to C. A1 waits at C.
    # T4: A1 & A2 both at C. A1 uses Lever. Success!
    
    sim.run(max_ticks=8)
    print("Run complete. Check phase21_run.jsonl")

if __name__ == "__main__":
    main()
