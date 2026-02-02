from typing import Dict, List, Optional
from src.entity import Entity, Agent, Object

class World:
    """
    The World class holds the state of the simulation.
    It separates the static graph (locations) from the dynamic state (entities).
    """
    def __init__(self):
        # The map graph: location_id -> { "neighbors": [], "objects": [] }
        # Objects here refers to IDs of objects present in the location
        self.locations: Dict[str, Dict] = {}
        
        # The global registry of all entities: entity_id -> Entity
        self.entities: Dict[str, Entity] = {}
        
        # Agent registry: agent_id -> Agent (subset of entities for quick access)
        self.agents: Dict[str, Agent] = {}

    def add_location(self, loc_id: str, neighbors: List[str] = None):
        """Adds a location node to the world graph."""
        if neighbors is None:
            neighbors = []
        self.locations[loc_id] = {
            "neighbors": neighbors,
            "objects": [] # List of Object IDs
        }

    def add_entity(self, entity: Entity):
        """Registers an entity in the global state."""
        self.entities[entity.id] = entity
        
        if isinstance(entity, Agent):
            self.agents[entity.id] = entity
        
        # If it has a location, update the location index
        if hasattr(entity, 'location_id') and entity.location_id in self.locations:
             # For objects, we track them in the location's object list
             # For agents, we might just track them by iterating agents (or add to location too)
             # Design choice: Let's track Objects in location metadata for easy lookup
             if isinstance(entity, Object):
                 self.locations[entity.location_id]["objects"].append(entity.id)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def get_neighbors(self, loc_id: str) -> List[str]:
        return self.locations.get(loc_id, {}).get("neighbors", [])
    
    def get_objects_at(self, loc_id: str) -> List[Object]:
        """Returns actual Object instances at a location."""
        obj_ids = self.locations.get(loc_id, {}).get("objects", [])
        return [self.entities[oid] for oid in obj_ids if oid in self.entities and isinstance(self.entities[oid], Object)]

    def move_agent(self, agent_id: str, new_loc_id: str):
        """
        Directly modifies state to move an agent. 
        Should only be called by the Simulation loop applying an Effect.
        """
        agent = self.agents.get(agent_id)
        if agent:
            # Note: We don't track agents in self.locations["objects"] to keep lists clean,
            # but we could if we wanted spatial hashing. For now, agents track their own loc.
            agent.location_id = new_loc_id

    def unlist_object(self, object_id: str):
        """Removes an object from its location index but keeps it in entities."""
        if object_id in self.entities:
            obj = self.entities[object_id]
            if isinstance(obj, Object) and obj.location_id in self.locations:
                if object_id in self.locations[obj.location_id]["objects"]:
                    self.locations[obj.location_id]["objects"].remove(object_id)
                obj.location_id = "" # Now in limbo or inventory

    def add_object_to_location(self, object_id: str, loc_id: str):
        """Adds an existing object to a location's index."""
        if object_id in self.entities and loc_id in self.locations:
            obj = self.entities[object_id]
            if isinstance(obj, Object):
                obj.location_id = loc_id
                if object_id not in self.locations[loc_id]["objects"]:
                    self.locations[loc_id]["objects"].append(object_id)

    def remove_object(self, object_id: str):
        """Removes an object from existence."""
        self.unlist_object(object_id)
        if object_id in self.entities:
            del self.entities[object_id]
