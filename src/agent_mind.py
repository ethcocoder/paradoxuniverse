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
    Phase 3: Cognitive Map & Communication.
    """
    
    SURVIVAL_THRESHOLD = 30
    BOREDOM_MAX = 5
    MEMORY_SIZE = 10
    COMM_ENERGY_THRESHOLD = 50 # Only talk if healthy
    
    @staticmethod
    def perceive(world: World, agent: Agent) -> Dict[str, Any]:
        """
        Gathers data AND updates internal cognitive map (Perception is active).
        """
        current_loc = agent.location_id
        objects = world.get_objects_at(current_loc)
        visible_food = [o.id for o in objects if o.type == ObjectType.FOOD]
        visible_hazards = [o.id for o in objects if o.type == ObjectType.HAZARD] # Phase 13
        # Phase 15: Cooperative Resource Details
        visible_coop_food = []
        for o in objects:
            if o.type == ObjectType.COOP_FOOD:
                visible_coop_food.append({
                    "id": o.id,
                    "required": o.required_agents,
                    "value": o.value
                })
        
        # Phase 20: Tools and Obstacles
        visible_tools = []
        visible_obstacles = []
        for o in objects:
            if o.type == ObjectType.TOOL:
                visible_tools.append({
                    "id": o.id,
                    "tool_type": o.tool_type
                })
            elif o.type == ObjectType.OBSTACLE:
                visible_obstacles.append({
                    "id": o.id,
                    "tool_required": o.tool_required
                })
        
        neighbors = world.get_neighbors(current_loc)
        
        # Phase 6: Perception of Agents
        # We need to find agents in the current location.
        # World.agents is a dict. We can iterate. In efficient system, World would provide get_agents_at(loc).
        # Let's rely on world.agents iteration for now (assuming small world).
        # Phase 6/14: Perception of Agents (In current AND adjacent locations)
        visible_agents = []
        # Current location
        for a_id, other in world.agents.items():
            if other.id != agent.id and other.is_alive:
                if other.location_id == current_loc:
                    visible_agents.append({
                        "id": other.id,
                        "location": other.location_id,
                        "energy": other.energy,
                        "last_action": other.last_action,
                        "distance": 0
                    })
                elif other.location_id in neighbors: # Phase 14: See into adjacent rooms
                    visible_agents.append({
                        "id": other.id,
                        "location": other.location_id,
                        "energy": other.energy,
                        "last_action": other.last_action,
                        "distance": 1
                    })
        
        perception = {
            "tick": agent.last_tick_updated,
            "location": current_loc,
            "energy": agent.energy,
            "visible_food": visible_food,
            "visible_hazards": visible_hazards, # Phase 13
            "visible_coop_food": visible_coop_food, # Phase 15
            "visible_tools": visible_tools, # Phase 20
            "visible_obstacles": visible_obstacles, # Phase 20
            "neighbors": neighbors,
            "visited_neighbors": [n for n in neighbors if n in agent.visited_locations],
            "visible_agents": visible_agents, # Phase 6
            "inventory": [obj.id for obj in agent.inventory] # Phase 12
        }
        
        # Update Memory
        agent.memory.append(perception)
        if len(agent.memory) > AgentMind.MEMORY_SIZE:
            agent.memory.pop(0)
        agent.visited_locations.add(current_loc)
        
        # Update Cognitive Map (Phase 3)
        if current_loc not in agent.cognitive_map:
             agent.cognitive_map[current_loc] = {}
        
        objs_list = []
        if visible_food: objs_list.append("FOOD")
        if visible_hazards: objs_list.append("HAZARD") # Phase 13
        if visible_coop_food: objs_list.append("COOP_FOOD") # Phase 15
        if visible_tools: objs_list.append("TOOL") # Phase 20
        if visible_obstacles: objs_list.append("OBSTACLE") # Phase 20
        
        # Store metadata for tools/obstacles (Phase 20)
        obj_metadata = {}
        if visible_tools:
            obj_metadata["tools"] = visible_tools
        if visible_obstacles:
            obj_metadata["obstacles"] = visible_obstacles
        
        agent.cognitive_map[current_loc].update({
             "neighbors": neighbors,
             "objects": objs_list,
             "metadata": obj_metadata,
             "last_tick": agent.last_tick_updated
        })
# Iterate visible agents and update social map
        for va in visible_agents:
            AgentSocial.update_seen_agent(agent, va["id"], va)
            
        # Phase 16: Reputation Tracking (Observe Participation)
        if len(agent.memory) >= 2:
            prev = agent.memory[-2] # Previous perception
            if prev.get("location") == current_loc:
                prev_coop = prev.get("visible_coop_food", [])
                if prev_coop and not visible_coop_food:
                    # Cooperative food was here, now it's gone!
                    # Crediting all agents who were present (distance 0) in BOTH ticks
                    prev_agents = {a["id"] for a in prev.get("visible_agents", []) if a["distance"] == 0}
                    curr_agents = {a["id"] for a in visible_agents if a["distance"] == 0}
                    participants = prev_agents.intersection(curr_agents)
                    for p_id in participants:
                        AgentSocial.update_reputation(agent, p_id, 0.5)
        
        # Phase 8: Update Long-Term Patterns
        MemoryAnalyzer.update_patterns(agent, perception)
            
        return perception

    @staticmethod
    def _update_map(agent: Agent, loc_id: str, neighbors: List[str], objects: List[str]):
        if loc_id not in agent.cognitive_map:
            agent.cognitive_map[loc_id] = {}
        
        agent.cognitive_map[loc_id]["neighbors"] = neighbors
        agent.cognitive_map[loc_id]["objects"] = objects # Simplified representation for map

    @staticmethod
    def decide(agent: Agent, perception: Dict[str, Any]) -> Action:
        # --- PHASE 17: STORY GENERATION (Must happen before returns) ---
        AgentSocial.generate_story(agent, perception)
        
        # --- PHASE 7: STRATEGIC GOAL SELECTION ---
        active_goal = GoalManager.select_top_goal(agent, perception)
        
        # Detect goal switch
        if agent.current_goal != active_goal.type.name:
            # Clear plan queue because old plan likely irrelevant
            if agent.plan_queue:
                agent.plan_queue = []
            
            agent.goal_history.append(agent.current_goal)
            agent.current_goal = active_goal.type.name
            # Sim should log this (we'll add that in sim.py)
            
        # 0. Communication Check (Phase 3 Legacy - Random Share)
        # --- PHASE 15: COOPERATIVE RESOURCE LOGIC ---
        coop_foods = perception.get("visible_coop_food", [])
        if coop_foods:
            # We assume only one for simplicity in choosing
            res = coop_foods[0]
            agents_here = 1 + len([a for a in perception["visible_agents"] if a["distance"] == 0])
            
            if agents_here >= res["required"]:
                # Success condition!
                return Action(ActionType.EXTRACT, target_id=res["id"])
            else:
                # Need backup!
                # Only call if we are relatively healthy (why waste others' time if you'll die?)
                if perception["energy"] > 20:
                     return Action(ActionType.COMMUNICATE, target_id="HELP_CALL")

        # --- PHASE 13: ALARM REFLEX ---
        if perception.get("visible_hazards"):
             # High priority: Warn others!
             return Action(ActionType.COMMUNICATE, target_id="ALARM")

        # We might want to keep or replace this with Social Logic. 
        
        # --- PHASE 6/14: SOCIAL COOPERATION & IMITATION ---
        if active_goal.type == GoalType.SOCIAL:
            social_action = AgentSocial.decide_cooperation(agent, perception)
            if social_action:
                # Prioritize direct help
                return social_action
            
            # Phase 17: Gossip (Share stories if no immediate help needed)
            # Find a neighbor to talk to
            listeners = [a for a in perception.get("visible_agents", []) if a["distance"] == 0]
            if listeners and agent.stories:
                target_listener = listeners[0]["id"] # Pick first
                story = AgentSocial.select_story_to_tell(agent, target_listener)
                if story:
                     # We use COMMUNICATE with 'STORY' type.
                     return Action(ActionType.COMMUNICATE, target_id=f"STORY:{target_listener}")
            
            # Phase 14: Imitation (Follow trusted peers)
            follow_target = AgentSocial.get_observation_to_imitate(agent, perception)
            if follow_target:
                return Action(ActionType.MOVE, target_id=follow_target)
            
        # --- 0. PRIORITY INTERRUPT: SURVIVAL ---
        # If hungry (even moderately) and food is right here, EAT IT immediately, ignoring plan.
        # Rationale: If I planned to go somewhere else, but I stumbled on food and I'm hungry, take it.
        if perception["energy"] < AgentMind.SURVIVAL_THRESHOLD and perception["visible_food"]:
             return Action(ActionType.CONSUME, target_id=perception["visible_food"][0])

        # --- PHASE 9 & 13: PLAN VALIDATION ---
        if agent.plan_queue:
            # 1. Imagination (Suicide Check)
            if not ForwardModel.is_plan_safe(agent, agent.plan_queue):
                agent.plan_queue = []
            
            # 2. Meta-Reflection (Hazard avoidance check) - Phase 13
            elif agent.plan_queue[0].type == ActionType.MOVE:
                target = agent.plan_queue[0].target_id
                if AgentMeta.get_score(agent, target) < -0.5:
                     # This room is now known to be bad! Abort.
                     agent.plan_queue = []
        
        # --- 1. EXECUTE PLAN (Phase 5) ---
        if agent.plan_queue:
            next_action = agent.plan_queue.pop(0)
            return next_action
            
        # --- 2. GOAL-BASED ACTION GENERATION ---
        
        # --- PHASE 20: REACTIVE INTERACTION (PICKUP/USE) ---
        # 1. Pickup required tools if they are here
        if perception.get("visible_tools"):
            tool_info = perception["visible_tools"][0]
            # If we don't have this specific tool, pick it up
            if not any(item.id == tool_info["id"] for item in agent.inventory):
                 return Action(ActionType.PICKUP, target_id=tool_info["id"])

        # 2. Use tool on obstacle if here and we have the requirement
        if perception.get("visible_obstacles"):
            for obs in perception["visible_obstacles"]:
                required = obs.get("tool_required")
                if not required or any(item.tool_type == required for item in agent.inventory):
                     return Action(ActionType.USE, target_id=obs["id"])

        # A. SURVIVAL GOAL
        if active_goal.type == GoalType.SURVIVAL:
            # Plan to find food
            new_plan = AgentPlanner.generate_plan(agent) # Planner prioritizes food
            if new_plan:
                # PHASE 9: Validate new plan
                if ForwardModel.is_plan_safe(agent, new_plan):
                    agent.plan_queue = new_plan
                    return agent.plan_queue.pop(0)
                else:
                    # Plan predicted to fail, maybe greedy fallback or wait
                    pass
            
            # Local fallback
            if perception["visible_food"]:
                return Action(ActionType.CONSUME, target_id=perception["visible_food"][0])
            if perception["neighbors"]:
                return AgentMind._choose_move(agent, perception)

        # B. EXPLORE GOAL
        if active_goal.type == GoalType.EXPLORE:
            # Phase 12: Territoriality - Set Home Base
            if not agent.home_location_id:
                agent.home_location_id = perception["location"]
            
            # Phase 12: Caching Logic (Hoarding)
            # If I'm rich and see food, and I'm NOT at home, pick it up to carry it back.
            if perception["energy"] > 80 and perception["visible_food"] and perception["location"] != agent.home_location_id:
                return Action(ActionType.PICKUP, target_id=perception["visible_food"][0])
            
            # If I'm carrying food and at home, drop it.
            if agent.inventory and perception["location"] == agent.home_location_id:
                # Only drop if it's FOOD (Phase 20 fix: don't drop tools we need!)
                food_item = next((o for o in agent.inventory if o.type == ObjectType.FOOD), None)
                if food_item:
                    return Action(ActionType.DROP, target_id=food_item.id)
            
            new_plan = AgentPlanner.generate_plan(agent) # Planner finds frontiers
            if new_plan:
                agent.plan_queue = new_plan
                return agent.plan_queue.pop(0)
            
            # Local fallback
            if perception["neighbors"]:
                return AgentMind._choose_move(agent, perception)

        # C. SOCIAL (Already handled above for immediate help, fallback wait)
        if active_goal.type == GoalType.SOCIAL:
             return Action(ActionType.WAIT)
             
        return Action(ActionType.WAIT)

    @staticmethod
    def _find_food_in_map(agent: Agent, reachable_neighbors: List[str]) -> str:
        """Checks reachable neighbors in map for 'FOOD' tag."""
        for n in reachable_neighbors:
            node_data = agent.cognitive_map.get(n)
            if node_data:
                objs = node_data.get("objects", [])
                if "FOOD" in objs: # stored as string in _update_map
                    return n
        return ""

    @staticmethod
    def _choose_move(agent: Agent, perception: Dict[str, Any]) -> Action:
        neighbors = perception["neighbors"]
        if not neighbors:
            return Action(ActionType.WAIT)
            
        unvisited = [n for n in neighbors if n not in agent.visited_locations]
        
        # Phase 4/10 Update: Filter by Reflection Score and IMAGINATION
        def is_safe(n):
            # 1. Meta-Reflection (Avoid dangerous history)
            # 2. Imagination (Avoid suicidal physics)
            
            meta_safe = AgentMeta.get_score(agent, n) >= -0.5
            
            # Check if move is suicidal
            test_plan = [Action(ActionType.MOVE, target_id=n)]
            imagined_safe = ForwardModel.is_plan_safe(agent, test_plan, survival_threshold=5.0)
            
            return meta_safe and imagined_safe
            
        safe_unvisited = [n for n in unvisited if is_safe(n)]
        safe_neighbors = [n for n in neighbors if is_safe(n)]
        
        target = ""
        if safe_unvisited:
            target = random.choice(safe_unvisited)
        elif safe_neighbors:
             # Fallback to visited but safe
             target = random.choice(safe_neighbors)
        else:
             # NO SAFE MOVES FOUND
             # Instead of picking randomly and dying, we WAIT
             return Action(ActionType.WAIT)
             
        return Action(ActionType.MOVE, target_id=target)
