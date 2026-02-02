import random
from typing import Optional, Callable
from src.world import World
from src.physics import Physics, Action, ActionType
from src.entity import Agent, Object
from src.logger import Logger
from src.agent_mind import AgentMind
from src.agent_communication import AgentCommunication
from src.agent_meta import AgentMeta
from src.agent_social import AgentSocial

class Simulation:
    def __init__(self, log_path="simulation.log", seed=42):
        self.world = World()
        self.logger = Logger(log_path)
        self.tick_count = 0
        self.seed = seed
        random.seed(seed)
        
    def run(self, max_ticks: int, agent_controller: Optional[Callable[[Agent, World], Action]] = None):
        """
        Main run loop.
        agent_controller: Function(agent, world) -> Action. 
                          If None, simple random walk is used.
        """
        print(f"Starting simulation with seed {self.seed} for {max_ticks} ticks.")
        
        for _ in range(max_ticks):
            self.tick(agent_controller)
            
            # Check stop condition (all agents dead)
            if not any(a.is_alive for a in self.world.agents.values()):
                print("All agents dead. Stopping.")
                break

    def tick(self, agent_controller: Optional[Callable[[Agent, World], Action]] = None):
        """
        Executes one atomic tick of the universe.
        Order:
        1. Global World Updates (if any)
        2. Per Agent:
           a. Apply Metabolism (Physics)
           b. Decide Action (Controller)
           c. Apply Action (Physics)
           d. Update World State (Commit)
           e. Log
        3. Increment Time
        """
        
        # Snapshot agent IDs to iterate safely
        agent_ids = list(self.world.agents.keys())
        
        for agent_id in agent_ids:
            agent = self.world.agents[agent_id]
            agent.last_tick_updated = self.tick_count # Sync perception time
            if not agent.is_alive:
                continue

            # --- 2a. Metabolism ---
            metabolic_effect = Physics.apply_tick_metabolism(self.world, agent)
            self._apply_effect(metabolic_effect)
            
            if not agent.is_alive:
                continue
            
            # --- 2a. Receive Messages (New Phase 3) ---
            msgs_processed = AgentCommunication.process_messages(agent)
            if msgs_processed > 0:
                 self.logger.log(self.tick_count, "INFO_UPDATE", {"agent_id": agent.id, "msgs": msgs_processed})

            # --- 2b. Mind: Perceive & Decide ---
            
            # 1. Perceive
            perception = AgentMind.perceive(self.world, agent)
            self.logger.log(self.tick_count, "PERCEPTION", {"agent_id": agent.id, "data": perception})
            
            # Track previous plan state to detect new plans
            was_planning = len(agent.plan_queue) > 0
            
            # Track goal for logging
            old_goal = agent.current_goal
            
            # 2. Decide
            if agent_controller:
                # Override for manual/testing control
                action = agent_controller(agent, self.world)
            else:
                action = AgentMind.decide(agent, perception)
            
            # Phase 14: Social observation
            agent.last_action = action
            
            # Phase 7: Goal Switch Logging
            if old_goal != agent.current_goal:
                 self.logger.log(self.tick_count, "GOAL_SWITCH", {
                     "agent_id": agent.id,
                     "old": old_goal,
                     "new": agent.current_goal
                 })
            
            # Phase 9: Imagination Abort Logging
            if was_planning and not agent.plan_queue: 
                 self.logger.log(self.tick_count, "IMAGINATION_ABORT", {
                     "agent_id": agent.id,
                     "reason": "Predicted failure"
                 })
            
            # Check for new plan generation
            if not was_planning and len(agent.plan_queue) > 0:
                 self.logger.log(self.tick_count, "PLAN_GENERATED", {
                     "agent_id": agent.id, 
                     "target": agent.planned_target, # We need to ensure Planner sets this or Mind sets this? 
                     # Mind didn't set planned_target in my previous edit. 
                     # Let's just log length for now, or update Mind to set it.
                     "steps": len(agent.plan_queue) + 1 # +1 for the current action just invoked?
                     # Actually decide() pops the first action. So queue has rest. 
                     # Total steps = len(queue) + 1
                 })
                
            self.logger.log(self.tick_count, "DECISION", {"agent_id": agent.id, "action": str(action.type.name), "target": action.target_id})

            # --- 2c. Apply Action Rule ---
            action_effect = Physics.apply_action(self.world, agent, action)
            
            # Phase 5: Plan Maintenance
            if not action_effect.success and agent.plan_queue:
                # Plan failed (e.g. path blocked), clear remainder to trigger re-planning
                agent.plan_queue = []
                action_effect.message += " (Plan Aborted)"
            
            if action_effect.success and action_effect.action.type == ActionType.COMMUNICATE:
                 target_id = action_effect.action.target_id
                 if target_id == "ALARM":
                      # Phase 13: ALARM CALL
                      # Signal hazard at current location to everyone!
                      payload = {"location_id": agent.location_id}
                      all_agents = list(self.world.agents.values())
                      AgentCommunication.broadcast(self.world, agent, all_agents, payload, msg_type="ALARM")
                      self.logger.log(self.tick_count, "ALARM_CHIRP", {"sender": agent.id, "location": agent.location_id})
                 elif target_id == "HELP_CALL":
                       # Phase 15: COOP HELP CALL
                       payload = {"location_id": agent.location_id, "type": "COOP_RESOURCE"}
                       all_agents = list(self.world.agents.values())
                       AgentCommunication.broadcast(self.world, agent, all_agents, payload, msg_type="HELP_CALL")
                       self.logger.log(self.tick_count, "HELP_CALL_SENT", {"sender": agent.id, "location": agent.location_id})
                 elif target_id and target_id.startswith("PUZZLE_HELP:"):
                       # Phase 21: Social Puzzle Help
                       puzzle_id = target_id.split(":")[1]
                       # Find puzzle metadata
                       puzzle = self.world.get_entity(puzzle_id)
                       payload = {
                           "location_id": agent.location_id,
                           "puzzle_id": puzzle_id,
                           "metadata": {
                               "obstacles": [{
                                   "id": puzzle.id,
                                   "tool_required": puzzle.tool_required,
                                   "required_agents": puzzle.required_agents
                               }]
                           }
                       }
                       all_agents = list(self.world.agents.values())
                       AgentCommunication.broadcast(self.world, agent, all_agents, payload, msg_type="PUZZLE_HELP")
                       self.logger.log(self.tick_count, "PUZZLE_HELP_SENT", {"sender": agent.id, "location": agent.location_id, "puzzle": puzzle_id})
                 elif target_id.startswith("STORY:"):
                       # Phase 17: Gossip
                       real_target_id = target_id.split(":")[1]
                       if real_target_id in self.world.agents:
                           receiver = self.world.agents[real_target_id]
                           story_payload = AgentSocial.select_story_to_tell(agent, real_target_id)
                           if story_payload:
                                AgentCommunication.broadcast(self.world, agent, [receiver], story_payload, msg_type="STORY")
                                self.logger.log(self.tick_count, "STORY_SHARED", {"sender": agent.id, "receiver": real_target_id, "topic": story_payload["topic"]})
                 elif target_id and target_id in self.world.agents:
                      # TARGETED SHARE
                      target_agent = self.world.agents[target_id]
                      # Identify highest value info (Phase 11)
                      high_value_payload = AgentSocial.identify_highest_value_info(agent)
                      if high_value_payload:
                           # Wrap in a dict format compatible with _merge_map (loc_id: {objects: []})
                           loc_id = high_value_payload["location_id"]
                           payload = {loc_id: {"objects": ["FOOD"]}}
                           AgentCommunication.broadcast(self.world, agent, [target_agent], payload)
                           self.logger.log(self.tick_count, "ALTRUISTIC_ACTION", {
                               "sender": agent.id, 
                               "receiver": target_id, 
                               "info": high_value_payload
                           })
                      else:
                           # Fallback to whole map
                           AgentCommunication.broadcast(self.world, agent, [target_agent], agent.cognitive_map)
                 else:
                      # Execute Broadcast
                      payload = agent.cognitive_map
                      all_agents = list(self.world.agents.values())
                      AgentCommunication.broadcast(self.world, agent, all_agents, payload)
                      self.logger.log(self.tick_count, "COMMUNICATION", {"sender": agent.id, "receivers": len(all_agents)-1, "payload_size": len(payload)})

            # --- 2d. Update World State ---
            self._apply_effect(action_effect)
            
            # --- 2e. History & Reflection (Phase 4) ---
            # Record history
            history_entry = {
                "tick": self.tick_count,
                "action": action_effect.action, # Storing the Action object
                "success": action_effect.success,
                "energy_cost": action_effect.energy_cost
            }
            agent.action_history.append(history_entry)
            
            # Reflect
            AgentMeta.reflect(agent)
            
            # Log Reflection if Score Changed (Optional, or just periodic)
            # For verification, let's log any negative score update? 
            # Or just log current negative scores occasionally.
            # Let's log if reflection modified (hard to track diff, so just log "REFLECTION" event periodically)
            # Log Reflection & Social Status
            if self.tick_count % 5 == 0:
                 bad_scores = {k:v for k,v in agent.reflection_score.items() if v < 0}
                 if bad_scores:
                      self.logger.log(self.tick_count, "REFLECTION", {"agent_id": agent.id, "avoid_list": bad_scores})
                 
                 # Phase 6: Social Log
                 if agent.trust_scores:
                      self.logger.log(self.tick_count, "SOCIAL_STATUS", {"agent_id": agent.id, "trust": agent.trust_scores})

            # --- 2f. Log ---
            self.logger.log_effect(self.tick_count, metabolic_effect)
            self.logger.log_effect(self.tick_count, action_effect)
            
            # Log agent state summary
            self.logger.log(self.tick_count, "STATE", {
                "agent_id": agent.id,
                "loc": agent.location_id,
                "energy": agent.energy,
                "alive": agent.is_alive
            })

        self.tick_count += 1

    def _apply_effect(self, effect):
        """
        Commits the effect to the world state.
        This is the ONLY place state changes happen.
        """
        agent = self.world.agents.get(effect.agent_id)
        if not agent:
            return

        # 1. Apply costs/gains
        agent.energy -= effect.energy_cost
        agent.energy += effect.energy_gain
        
        if agent.energy <= 0:
            agent.is_alive = False
            self.logger.log(self.tick_count, "DEATH", {"agent_id": agent.id, "reason": "Starvation"})

        if not effect.success:
            return

        # Phase 22: Reward skill experience on success
        if effect.action.type == ActionType.EXTRACT:
            agent.skills["EXTRACT"] += 0.1
        elif effect.action.type == ActionType.USE:
            agent.skills["USE"] += 0.1
        elif effect.action.type == ActionType.MOVE:
            agent.skills["EXPLORE"] += 0.02 # Slower gain as movement is frequent

        # 2. Apply Location Change
        if effect.new_location_id:
            self.world.move_agent(effect.agent_id, effect.new_location_id)
            
        # 3. Apply Object Transfers (Phase 12)
        if effect.action.type == ActionType.PICKUP:
            obj_id = effect.action.target_id
            obj = self.world.get_entity(obj_id)
            if obj and isinstance(obj, Object):
                self.world.unlist_object(obj_id)
                agent.inventory.append(obj)
                self.logger.log(self.tick_count, "INVENTORY_ADD", {"agent_id": agent.id, "object_id": obj_id})
        
        elif effect.action.type == ActionType.DROP:
            obj_id = effect.action.target_id
            obj = next((o for o in agent.inventory if o.id == obj_id), None)
            if obj:
                agent.inventory.remove(obj)
                self.world.add_object_to_location(obj_id, agent.location_id)
                self.logger.log(self.tick_count, "INVENTORY_REMOVE", {"agent_id": agent.id, "object_id": obj_id})

        # 4. Apply Object Removal (e.g. Consumed or Extracted)
        if effect.removed_object_id:
            if effect.action.type == ActionType.CONSUME:
                self.world.remove_object(effect.removed_object_id)
            elif effect.action.type == ActionType.EXTRACT:
                self.world.remove_object(effect.removed_object_id)
                # Phase 16: List all participants at location
                participants = [a_id for a_id, a in self.world.agents.items() if a.location_id == agent.location_id and a.is_alive]
                self.logger.log(self.tick_count, "COOP_EXTRACTION", {
                    "agent_id": agent.id, 
                    "object_id": effect.removed_object_id,
                    "participants": participants
                })
            elif effect.action.type == ActionType.USE:
                self.world.remove_object(effect.removed_object_id)
                self.logger.log(self.tick_count, "OBJECT_USED", {"agent_id": agent.id, "object_id": effect.removed_object_id})
