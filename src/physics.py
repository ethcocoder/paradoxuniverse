from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum, auto
from src.entity import Agent, Object, ObjectType
from src.world import World

class ActionType(Enum):
    WAIT = auto()
    MOVE = auto()
    CONSUME = auto()
    COMMUNICATE = auto()
    PICKUP = auto() # Phase 12
    DROP = auto()   # Phase 12
    EXTRACT = auto() # Phase 15: Cooperative extraction
    USE = auto()     # Phase 20: Tool use on Obstacles

@dataclass
class Action:
    type: ActionType
    target_id: Optional[str] = None # For move (location_id) or consume (object_id)

@dataclass
class Effect:
    agent_id: str
    action: Action
    success: bool
    energy_cost: int = 0
    energy_gain: int = 0
    new_location_id: Optional[str] = None
    removed_object_id: Optional[str] = None
    added_object: Optional[Object] = None # For dropping items
    message: str = ""

class Physics:
    """
    Stateless rules engine.
    Principled: Inputs (World, Agent, Action) -> Output (Effect).
    Does NOT modify the world structure.
    """
    
    METABOLISM_COST = 1
    MOVE_COST = 5
    COMM_COST = 2 # Energy cost to broadcast
    PICKUP_COST = 2
    DROP_COST = 1
    EXTRACT_COST = 3 # Phase 15
    USE_COST = 2     # Phase 20
    
    @staticmethod
    def get_valid_actions(world: World, agent: Agent) -> List[Action]:
        """Returns a list of valid actions for an agent in the current state."""
        actions = [Action(ActionType.WAIT)]
        
        # Move actions
        current_loc = agent.location_id
        if current_loc in world.locations:
            neighbors = world.locations[current_loc].get("neighbors", [])
            for n_id in neighbors:
                actions.append(Action(ActionType.MOVE, target_id=n_id))
        
        # Consume actions
        objects = world.get_objects_at(current_loc)
        for obj in objects:
            if obj.type == ObjectType.FOOD:
                actions.append(Action(ActionType.CONSUME, target_id=obj.id))
            elif obj.type == ObjectType.COOP_FOOD: # Phase 15
                actions.append(Action(ActionType.EXTRACT, target_id=obj.id))
        
        # Always can communicate
        actions.append(Action(ActionType.COMMUNICATE))
        
        # Drop actions (if inventory not empty)
        for obj in agent.inventory:
            actions.append(Action(ActionType.DROP, target_id=obj.id))
                
        return actions

    @staticmethod
    def apply_action(world: World, agent: Agent, action: Action) -> Effect:
        """Determines the outcome of an action."""
        if action.type == ActionType.MOVE:
            return Physics._rule_move(world, agent, action.target_id)
        elif action.type == ActionType.CONSUME:
            return Physics._rule_consume(world, agent, action.target_id)
        elif action.type == ActionType.COMMUNICATE:
            # Physics only handles the metadata/energy part. 
            # The actual message passing happens in Sim/Communication layer,
            # OR we return a specific effect that Sim executes.
            return Effect(
                agent_id=agent.id, 
                action=action, 
                success=True, 
                energy_cost=Physics.COMM_COST, 
                message="Broadcasted info"
            )
        elif action.type == ActionType.PICKUP:
            return Physics._rule_pickup(world, agent, action.target_id)
        elif action.type == ActionType.DROP:
            return Physics._rule_drop(world, agent, action.target_id)
        elif action.type == ActionType.EXTRACT:
            return Physics._rule_extract(world, agent, action.target_id)
        elif action.type == ActionType.USE:
            return Physics._rule_use(world, agent, action.target_id)
        elif action.type == ActionType.WAIT:
            return Effect(agent.id, action, success=True, energy_cost=0, message="Waited")
        
        return Effect(agent.id, action, success=False, message="Unknown action")

    @staticmethod
    def apply_tick_metabolism(world: World, agent: Agent) -> Effect:
        """Calculates metabolic cost for existing + environmental hazards."""
        cost = Physics.METABOLISM_COST
        
        # Check for Hazards at location
        objects = world.get_objects_at(agent.location_id)
        for obj in objects:
            if obj.type == ObjectType.HAZARD:
                cost += obj.value # Hazard value counts as damage (e.g. 10 energy)
                
        return Effect(
            agent_id=agent.id,
            action=Action(ActionType.WAIT), # implicit
            success=True,
            energy_cost=cost,
            message="Metabolism + Hazard" if cost > Physics.METABOLISM_COST else "Metabolism"
        )

    @staticmethod
    def _rule_move(world: World, agent: Agent, target_loc_id: str) -> Effect:
        # 1. Check connectivity
        current_loc = agent.location_id
        neighbors = world.get_neighbors(current_loc)
        
        if target_loc_id not in neighbors:
            return Effect(agent.id, Action(ActionType.MOVE, target_loc_id), success=False, message=f"Cannot move to {target_loc_id} from {current_loc}")
            
        # 2. Check energy
        if agent.energy < Physics.MOVE_COST:
             return Effect(agent.id, Action(ActionType.MOVE, target_loc_id), success=False, message="Not enough energy")
             
        # 3. Success
        return Effect(
            agent_id=agent.id,
            action=Action(ActionType.MOVE, target_loc_id),
            success=True,
            energy_cost=Physics.MOVE_COST,
            new_location_id=target_loc_id,
            message=f"Moved to {target_loc_id}"
        )

    @staticmethod
    def _rule_consume(world: World, agent: Agent, target_obj_id: str) -> Effect:
        # 1. Check object exists at location
        current_loc = agent.location_id
        objects_at_loc = world.get_objects_at(current_loc)
        target_obj = next((o for o in objects_at_loc if o.id == target_obj_id), None)
        
        if not target_obj:
             return Effect(agent.id, Action(ActionType.CONSUME, target_obj_id), success=False, message="Object not found")
             
        # 2. Check if consumable
        if target_obj.type != ObjectType.FOOD:
            return Effect(agent.id, Action(ActionType.CONSUME, target_obj_id), success=False, message="Cannot eat that")
            
        # 3. Success
        return Effect(
            agent_id=agent.id,
            action=Action(ActionType.CONSUME, target_obj_id),
            success=True,
            energy_cost=0,
            energy_gain=target_obj.value,
            removed_object_id=target_obj_id,
            message=f"Ate {target_obj.type.name}"
        )

    @staticmethod
    def _rule_pickup(world: World, agent: Agent, target_obj_id: str) -> Effect:
        # 1. Check object exists at location
        current_loc = agent.location_id
        objects_at_loc = world.get_objects_at(current_loc)
        target_obj = next((o for o in objects_at_loc if o.id == target_obj_id), None)
        
        if not target_obj:
             return Effect(agent.id, Action(ActionType.PICKUP, target_obj_id), success=False, message="Object not found")
             
        # 2. Check energy
        if agent.energy < Physics.PICKUP_COST:
            return Effect(agent.id, Action(ActionType.PICKUP, target_obj_id), success=False, message="Not enough energy")
            
        # 3. Success
        return Effect(
            agent_id=agent.id,
            action=Action(ActionType.PICKUP, target_obj_id),
            success=True,
            energy_cost=Physics.PICKUP_COST,
            removed_object_id=target_obj_id,
            message=f"Picked up {target_obj.type.name}"
        )

    @staticmethod
    def _rule_drop(world: World, agent: Agent, target_obj_id: str) -> Effect:
        # 1. Check object in inventory
        target_obj = next((o for o in agent.inventory if o.id == target_obj_id), None)
        
        if not target_obj:
             return Effect(agent.id, Action(ActionType.DROP, target_obj_id), success=False, message="Object not in inventory")
             
        # 2. Check energy
        if agent.energy < Physics.DROP_COST:
            return Effect(agent.id, Action(ActionType.DROP, target_obj_id), success=False, message="Not enough energy")
            
        # 3. Success
        return Effect(
            agent_id=agent.id,
            action=Action(ActionType.DROP, target_obj_id),
            success=True,
            energy_cost=Physics.DROP_COST,
            added_object=target_obj,
            message=f"Dropped {target_obj.type.name}"
        )

    @staticmethod
    def _rule_extract(world: World, agent: Agent, target_obj_id: str) -> Effect:
        # 1. Check object exists
        obj = world.get_entity(target_obj_id)
        if not obj or not isinstance(obj, Object) or obj.location_id != agent.location_id:
             return Effect(agent.id, Action(ActionType.EXTRACT, target_obj_id), success=False, message="Object not found at location")
             
        # 2. Check energy
        if agent.energy < Physics.EXTRACT_COST:
             return Effect(agent.id, Action(ActionType.EXTRACT, target_obj_id), success=False, message="Not enough energy")
             
        # 3. Check cooperation (Phase 15)
        agents_here = [a for a in world.agents.values() if a.location_id == agent.location_id and a.is_alive]
        if len(agents_here) < obj.required_agents:
             return Effect(agent.id, Action(ActionType.EXTRACT, target_obj_id), success=False, message=f"Need {obj.required_agents} agents, only {len(agents_here)} present")
             
        # 4. Success
        return Effect(
            agent_id=agent.id,
            action=Action(ActionType.EXTRACT, target_obj_id),
            success=True,
            energy_cost=Physics.EXTRACT_COST,
            energy_gain=obj.value, # Shared reward (Sim will handle if it's per agent or split)
            removed_object_id=target_obj_id,
            message=f"Successfully extracted {obj.id}"
        )

    @staticmethod
    def _rule_use(world: World, agent: Agent, target_obj_id: str) -> Effect:
        """
        Rule for using tools on obstacles.
        Requires the correct tool to be in the agent's inventory.
        """
        # 1. Check object exists
        obj = world.get_entity(target_obj_id)
        if not obj or not isinstance(obj, Object) or obj.location_id != agent.location_id:
             return Effect(agent.id, Action(ActionType.USE, target_obj_id), success=False, message="Obstacle not found at location")

        if obj.type != ObjectType.OBSTACLE:
            return Effect(agent.id, Action(ActionType.USE, target_obj_id), success=False, message="Target is not a usable obstacle.")

        # 2. Check energy
        if agent.energy < Physics.USE_COST:
             return Effect(agent.id, Action(ActionType.USE, target_obj_id), success=False, message="Not enough energy")

        # 3. Check for required tool
        required_tool = obj.tool_required
        if not required_tool:
            # If no tool is required, it works like a switch
            return Effect(
                agent_id=agent.id,
                action=Action(ActionType.USE, target_obj_id),
                success=True,
                energy_cost=Physics.USE_COST,
                removed_object_id=target_obj_id,
                message=f"Used {target_obj_id}"
            )

        # Check inventory for a tool that matches the required_tool name/type
        # We assume tool_type in the object matches the tool_required string of the obstacle
        has_tool = any(item.type == ObjectType.TOOL and item.tool_type == required_tool for item in agent.inventory)
        
        if not has_tool:
            return Effect(agent.id, Action(ActionType.USE, target_obj_id), success=False, message=f"Need a {required_tool} to use this.")

        # 4. Success
        return Effect(
            agent_id=agent.id,
            action=Action(ActionType.USE, target_obj_id),
            success=True,
            energy_cost=Physics.USE_COST,
            removed_object_id=target_obj_id,
            message=f"Successfully used tool on {obj.id}"
        )
