from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from src.physics import Physics, Action, ActionType

@dataclass
class SimulatedState:
    energy: float
    location_id: str
    alive: bool

class ForwardModel:
    """
    Phase 9: Internal Simulation & Forward Modeling.
    Allows an agent to predict outcomes of action sequences locally.
    """
    
    @staticmethod
    def simulate_plan(agent, plan: List[Action]) -> List[SimulatedState]:
        """
        Simulates the execution of a plan starting from current agent state.
        This represents the agent's 'imagination'.
        """
        current_energy = agent.energy
        current_loc = agent.location_id
        states = [SimulatedState(energy=current_energy, location_id=current_loc, alive=agent.is_alive)]
        
        for action in plan:
            # 1. Metabolism (Simulate Tick cost)
            current_energy -= Physics.METABOLISM_COST
            
            if current_energy <= 0:
                states.append(SimulatedState(energy=current_energy, location_id=current_loc, alive=False))
                break
            
            # 2. Action Effects
            if action.type == ActionType.MOVE:
                if current_energy >= Physics.MOVE_COST:
                    current_energy -= Physics.MOVE_COST
                    current_loc = action.target_id
                else:
                    # Plan fails internally due to low energy
                    # We mark as 'alive' but stuck
                    states.append(SimulatedState(energy=current_energy, location_id=current_loc, alive=True))
                    break
            elif action.type == ActionType.CONSUME:
                # Prediction: assume 50 energy gain from food (average)
                # or look up the specific object if possible.
                # For simplicity in 'imagination', we assume successful consumption
                # if the agent has it in its plan.
                current_energy += 50 
            elif action.type == ActionType.COMMUNICATE:
                current_energy -= Physics.COMM_COST
                
            states.append(SimulatedState(energy=current_energy, location_id=current_loc, alive=current_energy > 0))
            if current_energy <= 0:
                break
                
        return states

    @staticmethod
    def is_plan_safe(agent, plan: List[Action], survival_threshold: float = 5.0) -> bool:
        """
        Heuristic: Is the plan likely to kill the agent or leave it critically weak?
        """
        if not plan:
            return True
            
        results = ForwardModel.simulate_plan(agent, plan)
        
        # Check if any step leads to death
        for state in results:
            if not state.alive:
                return False
                
        # Check if final energy is above threshold
        if results[-1].energy < survival_threshold:
            return False
            
        return True
