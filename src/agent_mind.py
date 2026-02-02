import random
from typing import Dict, Any, List
from src.entity import Agent, ObjectType
from src.world import World
from src.physics import Action, ActionType, Physics
from src.agent_meta import AgentMeta
from src.agent_planner import AgentPlanner
from src.agent_social import AgentSocial
from src.agent_goals import GoalManager, GoalType
from src.agent_memory_pro import MemoryAnalyzer
from src.agent_imagination import ForwardModel

class AgentMind:
    """
    Phase 3+: Cognitive Map, Communication, and Emergency Reflexes.
    """
    
    SURVIVAL_THRESHOLD = 30 # Critical survival energy level
    BOREDOM_MAX = 5 # Phase 2: Trigger exploration if stuck
    MEMORY_SIZE = 10
    
    @staticmethod
    def perceive(world: World, agent: Agent) -> Dict[str, Any]:
        current_loc = agent.location_id
        objects = world.get_objects_at(current_loc)
        visible_food = [o.id for o in objects if o.type == ObjectType.FOOD]
        visible_hazards = [o.id for o in objects if o.type == ObjectType.HAZARD]
        
        visible_coop_food = []
        for o in objects:
            if o.type == ObjectType.COOP_FOOD:
                visible_coop_food.append({"id": o.id, "required": o.required_agents, "value": o.value})
        
        visible_tools = []
        visible_obstacles = []
        for o in objects:
            if o.type == ObjectType.TOOL:
                visible_tools.append({"id": o.id, "tool_type": o.tool_type})
            elif o.type == ObjectType.OBSTACLE:
                visible_obstacles.append({"id": o.id, "tool_required": o.tool_required, "required_agents": o.required_agents})
        
        neighbors = world.get_neighbors(current_loc)
        visible_agents = []
        for a_id, other in world.agents.items():
            if other.id != agent.id and other.is_alive:
                dist = 0 if other.location_id == current_loc else (1 if other.location_id in neighbors else -1)
                if dist >= 0:
                    visible_agents.append({
                        "id": other.id, "location": other.location_id, "energy": other.energy,
                        "last_action": other.last_action, "distance": dist
                    })
        
        perception = {
            "tick": agent.last_tick_updated, "location": current_loc, "energy": agent.energy,
            "visible_food": visible_food, "visible_hazards": visible_hazards,
            "visible_coop_food": visible_coop_food, "visible_tools": visible_tools,
            "visible_obstacles": visible_obstacles, "neighbors": neighbors,
            "visited_neighbors": [n for n in neighbors if n in agent.visited_locations],
            "visible_agents": visible_agents, "inventory": [obj.id for obj in agent.inventory]
        }
        
        agent.memory.append(perception)
        if len(agent.memory) > AgentMind.MEMORY_SIZE: agent.memory.pop(0)
        agent.visited_locations.add(current_loc)
        
        if current_loc not in agent.cognitive_map: agent.cognitive_map[current_loc] = {}
        objs_list = []
        if visible_food: objs_list.append("FOOD")
        if visible_hazards: objs_list.append("HAZARD")
        if visible_coop_food: objs_list.append("COOP_FOOD")
        if visible_tools: objs_list.append("TOOL")
        if visible_obstacles: objs_list.append("OBSTACLE")
        
        agent.cognitive_map[current_loc].update({
             "neighbors": neighbors, "objects": objs_list,
             "metadata": {"tools": visible_tools, "obstacles": visible_obstacles},
             "last_tick": agent.last_tick_updated
        })

        for va in visible_agents: AgentSocial.update_seen_agent(agent, va["id"], va)
            
        if len(agent.memory) >= 2:
            prev = agent.memory[-2]
            if prev.get("location") == current_loc:
                prev_coop = prev.get("visible_coop_food", [])
                if prev_coop and not visible_coop_food:
                    prev_agents = {a["id"] for a in prev.get("visible_agents", []) if a["distance"] == 0}
                    curr_agents = {a["id"] for a in visible_agents if a["distance"] == 0}
                    participants = prev_agents.intersection(curr_agents)
                    for p_id in participants: AgentSocial.update_reputation(agent, p_id, 0.5)
        
        MemoryAnalyzer.update_patterns(agent, perception)
        return perception

    @staticmethod
    def decide(agent: Agent, perception: Dict[str, Any]) -> Action:
        AgentSocial.generate_story(agent, perception)
        active_goal = GoalManager.select_top_goal(agent, perception)
        if agent.current_goal != active_goal.type.name:
            if agent.plan_queue: agent.plan_queue = []
            agent.goal_history.append(agent.current_goal)
            agent.current_goal = active_goal.type.name
            
        # --- 1. REACTIVE / IMMEDIATE ACTIONS ---
        
        # A. SURVIVAL INTERRUPT (Eat if at food and have room)
        if perception["energy"] < AgentMind.SURVIVAL_THRESHOLD and perception["visible_food"]:
             return Action(ActionType.CONSUME, target_id=perception["visible_food"][0])

        # B. REACTIVE INTERACTION (PICKUP/USE)
        if perception.get("visible_tools"):
            tool_info = perception["visible_tools"][0]
            if not any(item.id == tool_info["id"] for item in agent.inventory):
                 return Action(ActionType.PICKUP, target_id=tool_info["id"])

        if perception.get("visible_obstacles"):
            for obs in perception["visible_obstacles"]:
                required_agents = obs.get("required_agents", 1)
                agents_here = 1 + len([a for a in perception["visible_agents"] if a["distance"] == 0])
                if agents_here < required_agents:
                     if perception["energy"] > 20: return Action(ActionType.COMMUNICATE, target_id=f"PUZZLE_HELP:{obs['id']}")
                     return Action(ActionType.WAIT)
                required_tool = obs.get("tool_required")
                if not required_tool or any(item.tool_type == required_tool for item in agent.inventory):
                     return Action(ActionType.USE, target_id=obs["id"])

        # Home-based hoarding (only pick up food when at home with high energy)
        if (perception["energy"] >= 85 and perception["visible_food"] and 
            perception["location"] == agent.home_location_id):
            return Action(ActionType.PICKUP, target_id=perception["visible_food"][0])
        
        # Inventory management: Drop food at home
        if agent.inventory and perception["location"] == agent.home_location_id:
            food_item = next((o for o in agent.inventory if o.type == ObjectType.FOOD), None)
            if food_item: return Action(ActionType.DROP, target_id=food_item.id)

        # --- 2. PLAN EXECUTION ---
        if agent.plan_queue:
            if not ForwardModel.is_plan_safe(agent, agent.plan_queue):
                agent.plan_queue = []
            elif agent.plan_queue[0].type == ActionType.MOVE:
                target = agent.plan_queue[0].target_id
                if AgentMeta.get_score(agent, target) < -0.5: agent.plan_queue = []

        if agent.plan_queue:
            return agent.plan_queue.pop(0)

        # --- 3. GOAL-BASED ACTION GENERATION ---
        
        # Coop Food / Hazards
        coop_foods = perception.get("visible_coop_food", [])
        if coop_foods:
            res = coop_foods[0]
            agents_here = 1 + len([a for a in perception["visible_agents"] if a["distance"] == 0])
            if agents_here >= res["required"]: return Action(ActionType.EXTRACT, target_id=res["id"])
            elif perception["energy"] > 20: return Action(ActionType.COMMUNICATE, target_id="HELP_CALL")
        if perception.get("visible_hazards"): return Action(ActionType.COMMUNICATE, target_id="ALARM")

        # Goal Logics
        if active_goal.type == GoalType.SOCIAL:
            social_action = AgentSocial.decide_cooperation(agent, perception)
            if social_action: return social_action
            listeners = [a for a in perception.get("visible_agents", []) if a["distance"] == 0]
            if listeners and agent.stories:
                story = AgentSocial.select_story_to_tell(agent, listeners[0]["id"])
                if story: return Action(ActionType.COMMUNICATE, target_id=f"STORY:{listeners[0]['id']}")
            follow_target = AgentSocial.get_observation_to_imitate(agent, perception)
            if follow_target: return Action(ActionType.MOVE, target_id=follow_target)
            return Action(ActionType.WAIT)

        if active_goal.type == GoalType.SURVIVAL:
            new_plan = AgentPlanner.generate_plan(agent)
            if new_plan and ForwardModel.is_plan_safe(agent, new_plan):
                agent.plan_queue = new_plan
                return agent.plan_queue.pop(0)
            if perception["visible_food"]: return Action(ActionType.CONSUME, target_id=perception["visible_food"][0])

        if active_goal.type == GoalType.EXPLORE:
            if not agent.home_location_id: agent.home_location_id = perception["location"]
            
            # Consume food if present and not at full energy
            if perception["visible_food"] and perception["energy"] < 95:
                return Action(ActionType.CONSUME, target_id=perception["visible_food"][0])
            
            new_plan = AgentPlanner.generate_plan(agent)
            if new_plan:
                agent.plan_queue = new_plan
                return agent.plan_queue.pop(0)

        if perception["neighbors"]: return AgentMind._choose_move(agent, perception)
        return Action(ActionType.WAIT)

    @staticmethod
    def _choose_move(agent: Agent, perception: Dict[str, Any]) -> Action:
        neighbors = perception["neighbors"]
        if not neighbors: return Action(ActionType.WAIT)
        unvisited = [n for n in neighbors if n not in agent.visited_locations]
        
        def is_safe(n):
            meta_safe = AgentMeta.get_score(agent, n) >= -0.5
            test_plan = [Action(ActionType.MOVE, target_id=n)]
            return meta_safe and ForwardModel.is_plan_safe(agent, test_plan, survival_threshold=2.0)
            
        safe_unvisited = [n for n in unvisited if is_safe(n)]
        safe_neighbors = [n for n in neighbors if is_safe(n)]
        
        if safe_unvisited: target = random.choice(safe_unvisited)
        elif safe_neighbors: target = random.choice(safe_neighbors)
        else: return Action(ActionType.WAIT)
        return Action(ActionType.MOVE, target_id=target)
