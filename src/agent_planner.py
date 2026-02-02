from typing import List, Dict, Any, Optional
from collections import deque
from src.entity import Agent, ObjectType
from src.physics import Action, ActionType
from src.agent_memory_pro import MemoryAnalyzer
from src.agent_meta import AgentMeta

class AgentPlanner:
    """
    Phase 5: Advanced Planning.
    Generates multi-step plans based on Cognitive Map.
    """
    
    @staticmethod
    def generate_plan(agent: Agent) -> List[Action]:
        """
        Analyses map and returns a sequence of Actions to reach a goal.
        Priorities:
        1. Known Food (if hungry)
        2. Nearest Unexplored Frontier (Curiosity)
        """
        # 0. Basic Check
        current_loc = agent.location_id
        map_data = agent.cognitive_map
        
        if not map_data:
            return []

        # 1. Identify Goals
        goal_metrics = [] # (score, target_id, type)
        
        # Priority A: Food
        # Iterate all known nodes, check objects
        # Note: In Phase 3, we stored objects as strings in 'objects' list? 
        # Let's verify CognitiveMap structure from Phase 3 code in Sim/Communication.
        # It was: {loc_id: {"neighbors": [...], "objects": ["FOOD", ...]}}
        
        for loc, data in map_data.items():
            if loc == current_loc:
                continue
            
            # Check for Food
            # In Phase 3 we simplified objects to strings like "ObjectType.FOOD" or similar?
            # Let's assume standard string checks or Enum checks if stored as Enum.
            # Sim.py L87: payload = agent.cognitive_map
            # AgentMind perception stores: "objects": [o.type.name for o in obj_list]
            
            if "objects" in data:
                if "FOOD" in data["objects"]:
                    # Score based on distance (bfs distance) later, but high base score
                    goal_metrics.append((100, loc, "FOOD"))
                if "COOP_FOOD" in data["objects"]: # Phase 15
                    priority = 120
                    # Phase 16: Reputation influence
                    requester = data.get("requester_id")
                    if requester:
                        rep = agent.social_reputations.get(requester, 0.0) # -2.0 to 2.0
                        priority += rep * 20 # Can go from 80 to 160
                    goal_metrics.append((priority, loc, "COOP_FOOD"))

        # Priority B: Frontiers (Unvisited/Unmapped neighbors of known nodes)
        # Actually, "Unexplored" means we know it exists (neighbor) but have no entry for it in map?
        # OR we visited it but want to revisit?
        # Let's define Frontier: A node Id that appears in a neighbor list BUT is not a key in cognitive_map.
        # This represents "I know there is a room there, but I haven't been/mapped it".
        
        known_nodes = set(map_data.keys())
        potential_frontiers = set()
        for loc, data in map_data.items():
            for n in data.get("neighbors", []):
                if n not in known_nodes:
                    potential_frontiers.add(n)
        
        for f in potential_frontiers:
            goal_metrics.append((50, f, "FRONTIER"))
            
        # Priority C: Probabilistic Food (Phase 8/18)
        # If no known goals, use historical memory (spatial_patterns) to guess where food might be
        # Hierarchical: Plan to go to a "Region" (Location) that has high food hits.
        if True: # Always check, but priority handles selection
            # Iterate spatial_patterns
            for loc_id, stats in agent.spatial_patterns.items():
                if loc_id == current_loc: continue
                hits = stats.get("food_hits", 0)
                visits = stats.get("total_visits", 1)
                ratio = hits / max(1, visits)
                
                if ratio > 0.3: # Threshold for "Good Hunting Ground"
                    # Priority is lower than actual visible food (100) but can be higher than random frontier (50)
                    # Let's say 75.
                    if loc_id in map_data: # If we know how to get there
                        goal_metrics.append((75, loc_id, "LIKELY_REGION"))

        if not goal_metrics:
            likely_loc = MemoryAnalyzer.predict_resource_location(agent)
            if likely_loc and likely_loc != current_loc:
                goal_metrics.append((30, likely_loc, "PROBABLE_FOOD"))

        if not goal_metrics:
            return []
            
        # 2. Find Best Goal (Nearest High Score)
        # We need BFS for all goals to find distances
        
        best_plan = []
        best_score = -1
        
        # Optimization: BFS from Current Location outwards until we hit a goal?
        # Multi-target BFS.
        
        queue = deque([(current_loc, [])]) # (current_node, path_of_moves)
        visited = {current_loc}
        
        # We search until we find *any* goal? Or specific?
        # Simple approach: Search entire accessible graph, map distances.
        # Then pick goal with max (Score - DistanceCost).
        
        targets_found = {} # loc_id -> path
        
        while queue:
            curr, path = queue.popleft()
            
            # Check if this node is a goal
            targets_found[curr] = path
            
            # Expand neighbors
            # We can only move to neighbors we KNOW about (in cognitive_map)
            # OR if it's a frontier, we can move TO it (step 1), but can't expand FROM it (unknown).
            
            node_data = map_data.get(curr)
            if not node_data:
                # This could happen if curr is a frontier we just reached conceptually
                continue
                
            for n in node_data.get("neighbors", []):
                if n not in visited:
                    # Phase 13: Avoid dangerous areas in planning
                    if AgentMeta.get_score(agent, n) < -0.5:
                        continue
                        
                    visited.add(n)
                    new_path = path + [n]
                    queue.append((n, new_path))
        
        # Evaluate Goals
        for base_score, goal_id, g_type in goal_metrics:
            if goal_id in targets_found:
                path = targets_found[goal_id]
                cost = len(path)
                final_score = base_score - cost # Simple utility
                
                if final_score > best_score:
                    best_score = final_score
                    # Convert path to Actions
                    actions = [Action(ActionType.MOVE, target_id=step) for step in path]
                    best_plan = actions
                    
        return best_plan
