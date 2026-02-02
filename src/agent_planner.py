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
        current_loc = agent.location_id
        map_data = agent.cognitive_map
        if not map_data:
            return []

        # 1. Identify Goals
        goal_metrics = [] # (score, target_id, type)
        
        for loc, data in map_data.items():
            if loc == current_loc:
                continue
            
            if "objects" in data:
                # Phase 22: Skill multipliers
                extract_skill = agent.skills.get("EXTRACT", 1.0)
                use_skill = agent.skills.get("USE", 1.0)
                explore_skill = agent.skills.get("EXPLORE", 1.0)

                # Robust check for FOOD (string or Enum name)
                if any(x in data["objects"] for x in ["FOOD", "ObjectType.FOOD"]):
                    goal_metrics.append((100 * extract_skill, loc, "FOOD"))
                
                # Check for COOP_FOOD
                if any(x in data["objects"] for x in ["COOP_FOOD", "ObjectType.COOP_FOOD"]):
                    priority = 120
                    requester = data.get("requester_id")
                    if requester:
                        rep = agent.social_reputations.get(requester, 0.0)
                        priority += rep * 20
                    goal_metrics.append((priority * extract_skill, loc, "COOP_FOOD"))
            
                # Check for OBSTACLE
                if any(x in data["objects"] for x in ["OBSTACLE", "ObjectType.OBSTACLE"]):
                    obstacles = data.get("metadata", {}).get("obstacles", [])
                    for obs in obstacles:
                        required_tool_type = obs.get("tool_required")
                        if not required_tool_type:
                            goal_metrics.append((90, loc, "OBSTACLE"))
                            continue

                        has_tool = any(item.tool_type == required_tool_type for item in agent.inventory)
                        if has_tool:
                            goal_metrics.append((110 * use_skill, loc, "OBSTACLE"))
                        else:
                            # Search map for the tool
                            tool_loc = None
                            for t_loc, t_data in map_data.items():
                                tools = t_data.get("metadata", {}).get("tools", [])
                                if any(t.get("tool_type") == required_tool_type for t in tools):
                                    tool_loc = t_loc
                                    break
                            if tool_loc:
                                goal_metrics.append((115 * use_skill, tool_loc if tool_loc != current_loc else loc, "GET_TOOL"))
        
        # Frontiers
        known_nodes = set(map_data.keys())
        potential_frontiers = set()
        for loc, data in map_data.items():
            for n in data.get("neighbors", []):
                if n not in known_nodes:
                    potential_frontiers.add(n)
        
        explore_multi = agent.skills.get("EXPLORE", 1.0)
        for f in potential_frontiers:
            goal_metrics.append((50 * explore_multi, f, "FRONTIER"))
        
        # Stale Frontiers (Phase 19)
        STALE_THRESHOLD = 50
        current_tick = agent.last_tick_updated
        for loc, data in map_data.items():
            if loc == current_loc: continue
            last_tick = data.get("last_tick", 0)
            if current_tick - last_tick > STALE_THRESHOLD:
                goal_metrics.append((45, loc, "STALE_FRONTIER"))
            
        # Likely Regions (Phase 8/18)
        for loc_id, stats in agent.spatial_patterns.items():
            if loc_id == current_loc: continue
            hits = stats.get("food_hits", 0)
            visits = stats.get("total_visits", 1)
            ratio = hits / max(1, visits)
            if ratio > 0.3 and loc_id in map_data:
                goal_metrics.append((75, loc_id, "LIKELY_REGION"))

        if not goal_metrics:
            likely_loc = MemoryAnalyzer.predict_resource_location(agent)
            if likely_loc and likely_loc != current_loc:
                goal_metrics.append((30, likely_loc, "PROBABLE_FOOD"))

        if not goal_metrics:
            return []
            
        # 2. BFS for best goal
        def is_safe(n):
            return AgentMeta.get_score(agent, n) >= -0.5

        targets_found = {} # loc_id -> path
        queue = deque([(current_loc, [])])
        visited = {current_loc}
        
        while queue:
            curr, path = queue.popleft()
            targets_found[curr] = path
            
            node_data = map_data.get(curr)
            if not node_data: continue
                
            for n in node_data.get("neighbors", []):
                if n not in visited and is_safe(n):
                    visited.add(n)
                    queue.append((n, path + [n]))
        
        best_plan = []
        best_score = -1
        for base_score, goal_id, g_type in goal_metrics:
            if goal_id in targets_found:
                path = targets_found[goal_id]
                final_score = base_score - len(path)
                if final_score > best_score:
                    best_score = final_score
                    best_plan = [Action(ActionType.MOVE, target_id=step) for step in path]
                    
        return best_plan
